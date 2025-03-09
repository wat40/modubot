require('dotenv').config();
const express = require('express');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const fetch = require('node-fetch');
const path = require('path');
const cors = require('cors');

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Configure middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(session({
  secret: process.env.SESSION_SECRET || 'modubot-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { 
    secure: process.env.NODE_ENV === 'production',
    maxAge: 86400000 // 24 hours
  }
}));

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
const API_ROUTES = {
  AUTH: {
    LOGIN: '/api/auth/login',
    CALLBACK: '/api/auth/callback',
    LOGOUT: '/api/auth/logout'
  },
  USER: {
    PROFILE: '/api/user/profile',
    INVENTORY: '/api/user/inventory',
    BALANCE: '/api/user/balance',
    COLLECT: '/api/user/collect'
  },
  SHOP: {
    ITEMS: '/api/shop/items',
    PURCHASE: '/api/shop/purchase'
  },
  LEADERBOARD: '/api/leaderboard'
};

// Auth middleware
const isAuthenticated = (req, res, next) => {
  if (req.session.user) {
    return next();
  }
  res.status(401).json({ error: 'Unauthorized' });
};

// Discord OAuth routes
app.get(API_ROUTES.AUTH.LOGIN, (req, res) => {
  const { DISCORD_CLIENT_ID, DISCORD_REDIRECT_URI } = process.env;
  const scopes = ['identify', 'guilds'];
  
  const authUrl = new URL('https://discord.com/api/oauth2/authorize');
  authUrl.searchParams.append('client_id', DISCORD_CLIENT_ID);
  authUrl.searchParams.append('redirect_uri', DISCORD_REDIRECT_URI);
  authUrl.searchParams.append('response_type', 'code');
  authUrl.searchParams.append('scope', scopes.join(' '));
  
  res.redirect(authUrl.toString());
});

app.get(API_ROUTES.AUTH.CALLBACK, async (req, res) => {
  const { code } = req.query;
  
  if (!code) {
    return res.redirect('/?error=no_code');
  }
  
  try {
    const { DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI, DISCORD_API_URL } = process.env;
    
    // Exchange code for token
    const tokenResponse = await fetch(`${DISCORD_API_URL}/oauth2/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: DISCORD_CLIENT_ID,
        client_secret: DISCORD_CLIENT_SECRET,
        grant_type: 'authorization_code',
        code,
        redirect_uri: DISCORD_REDIRECT_URI,
        scope: 'identify guilds',
      }),
    });
    
    const tokenData = await tokenResponse.json();
    
    if (tokenData.error) {
      return res.redirect(`/?error=${tokenData.error}`);
    }
    
    // Fetch user data
    const userResponse = await fetch(`${DISCORD_API_URL}/users/@me`, {
      headers: {
        Authorization: `Bearer ${tokenData.access_token}`,
      },
    });
    
    const userData = await userResponse.json();
    
    // Store user in session
    req.session.user = {
      id: userData.id,
      username: userData.username,
      discriminator: userData.discriminator,
      avatar: userData.avatar,
      accessToken: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
    };
    
    res.redirect('/inventory.html?login_success=true');
  } catch (error) {
    console.error('OAuth error:', error);
    res.redirect('/?error=auth_error');
  }
});

app.get(API_ROUTES.AUTH.LOGOUT, (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

// User routes
app.get(API_ROUTES.USER.PROFILE, isAuthenticated, (req, res) => {
  // In a real app, you would fetch this from your database
  res.json({
    id: req.session.user.id,
    username: req.session.user.username,
    discriminator: req.session.user.discriminator,
    avatar: req.session.user.avatar,
    stats: {
      balance: 5280,
      incomeRate: 155,
      totalItems: 8,
      level: 5,
      xp: 1250,
      achievements: {
        unlocked: 2,
        total: 10
      }
    }
  });
});

app.get(API_ROUTES.USER.INVENTORY, isAuthenticated, (req, res) => {
  // In a real app, you would fetch this from your database
  res.json({
    passiveIncome: [
      {
        id: 'windmill',
        name: 'Windmill',
        description: 'Generates 15 coins per hour',
        imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464651057373204/windmill.png',
        incomeRate: 15,
        count: 1
      },
      {
        id: 'farm',
        name: 'Small Farm',
        description: 'Generates 40 coins per hour',
        imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464650784800888/farm.png',
        incomeRate: 40,
        count: 1
      },
      {
        id: 'mine',
        name: 'Gold Mine',
        description: 'Generates 100 coins per hour',
        imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464650487140382/mine.png',
        incomeRate: 100,
        count: 1
      }
    ],
    roles: [
      {
        id: 'vip',
        name: 'VIP Role',
        description: 'Special colored role for your server',
        imageUrl: 'https://cdn.discordapp.com/emojis/855054331787304980.webp?size=96&quality=lossless',
        equipped: true
      }
    ],
    consumables: [
      {
        id: 'mystery_box',
        name: 'Mystery Box',
        description: 'Contains random rewards',
        imageUrl: 'https://cdn.discordapp.com/emojis/1020679352279158814.webp?size=96&quality=lossless',
        count: 2
      }
    ],
    achievements: [
      {
        id: 'first_steps',
        name: 'First Steps',
        description: 'Make your first purchase from the shop',
        unlocked: true
      },
      {
        id: 'collector',
        name: 'Collector',
        description: 'Own one of each passive income item',
        unlocked: true
      },
      {
        id: 'big_spender',
        name: 'Big Spender',
        description: 'Spend a total of 100,000 coins in the shop',
        unlocked: false
      }
    ]
  });
});

app.get(API_ROUTES.USER.BALANCE, isAuthenticated, (req, res) => {
  // In a real app, you would fetch this from your database
  res.json({
    balance: 5280,
    incomeRate: 155,
    lastCollected: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1 hour ago
    availableIncome: 155
  });
});

app.post(API_ROUTES.USER.COLLECT, isAuthenticated, (req, res) => {
  // In a real app, this would update the database
  const { source } = req.body;
  let amount = 0;
  
  if (source === 'all') {
    amount = 342; // All available income
  } else if (source === 'windmill') {
    amount = 15;
  } else if (source === 'farm') {
    amount = 40;
  } else if (source === 'mine') {
    amount = 100;
  }
  
  // Add some variance
  const variance = Math.floor(amount * 0.2);
  amount += Math.floor(Math.random() * variance * 2) - variance;
  
  res.json({
    collected: amount,
    newBalance: 5280 + amount,
    newAvailableIncome: source === 'all' ? 0 : 342 - amount
  });
});

// Shop routes
app.get(API_ROUTES.SHOP.ITEMS, (req, res) => {
  res.json([
    {
      id: 'windmill',
      name: 'Windmill',
      description: 'Generates 15 coins per hour',
      imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464651057373204/windmill.png',
      price: 7500,
      incomeRate: 15,
      type: 'passive_income'
    },
    {
      id: 'farm',
      name: 'Small Farm',
      description: 'Generates 40 coins per hour',
      imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464650784800888/farm.png',
      price: 15000,
      incomeRate: 40,
      type: 'passive_income'
    },
    {
      id: 'mine',
      name: 'Gold Mine',
      description: 'Generates 100 coins per hour',
      imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464650487140382/mine.png',
      price: 30000,
      incomeRate: 100,
      type: 'passive_income'
    },
    {
      id: 'factory',
      name: 'Factory',
      description: 'Generates 180 coins per hour',
      imageUrl: 'https://cdn.discordapp.com/attachments/1348088564499480658/1348464650214551632/factory.png',
      price: 50000,
      incomeRate: 180,
      type: 'passive_income'
    },
    {
      id: 'vip',
      name: 'VIP Role',
      description: 'Special colored role for your server',
      imageUrl: 'https://cdn.discordapp.com/emojis/855054331787304980.webp?size=96&quality=lossless',
      price: 5000,
      type: 'role'
    },
    {
      id: 'mystery_box',
      name: 'Mystery Box',
      description: 'Contains random rewards',
      imageUrl: 'https://cdn.discordapp.com/emojis/1020679352279158814.webp?size=96&quality=lossless',
      price: 2500,
      type: 'consumable'
    }
  ]);
});

app.post(API_ROUTES.SHOP.PURCHASE, isAuthenticated, (req, res) => {
  const { itemId } = req.body;
  
  // In a real app, you would validate the purchase and update the database
  // For now, we'll just simulate a successful purchase
  res.json({
    success: true,
    message: 'Item purchased successfully!',
    item: {
      id: itemId,
      name: 'Item Name',
      type: 'passive_income'
    },
    newBalance: 5280 - 7500 // Just an example
  });
});

// Leaderboard route
app.get(API_ROUTES.LEADERBOARD, (req, res) => {
  const { category = 'balance' } = req.query;
  
  // In a real app, you would fetch this from your database
  const mockUsers = [
    { name: "User1", value: 10500, rank: 1 },
    { name: "User2", value: 8200, rank: 2 },
    { name: "User3", value: 7800, rank: 3 },
    { name: "User4", value: 6500, rank: 4 },
    { name: "CurrentUser", value: 5280, rank: 5 },
    { name: "User6", value: 4900, rank: 6 },
    { name: "User7", value: 3700, rank: 7 },
    { name: "User8", value: 2500, rank: 8 },
    { name: "User9", value: 1800, rank: 9 },
    { name: "User10", value: 1200, rank: 10 }
  ];
  
  res.json({
    category,
    entries: mockUsers
  });
});

// Main routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/inventory', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'inventory.html'));
});

// Handle 404s
app.use((req, res) => {
  res.status(404).sendFile(path.join(__dirname, 'public', '404.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`ModuBot Dashboard is running on port ${PORT}`);
  console.log(`Local: http://localhost:${PORT}`);
  console.log(`Discord Client ID: ${process.env.DISCORD_CLIENT_ID}`);
}); 