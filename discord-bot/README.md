# ModuBot - Discord Bot with Dashboard

This is a Discord bot with a comprehensive dashboard for managing server moderation, economy, and passive income features.

## Features

- **Slash Commands**: Fully supports Discord's slash command system
- **Moderation Commands**: Ban, kick, timeout, and message clearing functionality
- **Global Economy**: Cross-server economy system with currency and shop
- **Passive Income**: Invest in windmills, farms, mines and more to earn passive income
- **Web Dashboard**: Interactive web interface to manage your inventory and collect income
- **Discord OAuth**: Secure login with Discord OAuth2 integration

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- Discord Bot Token
- Discord Application with OAuth2 configured

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/modubot.git
cd modubot
```

2. Install dependencies
```bash
npm install
```

3. Configure environment variables
Create a `.env` file in the root directory with the following:
```
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:3000/api/auth/callback
SESSION_SECRET=your_session_secret
```

4. Start the server
```bash
npm start
```

The server will be available at http://localhost:3000

## Deployment on Glitch

1. Create a new project on Glitch
2. Import this project from GitHub
3. Set up the environment variables in the .env file
4. The bot will automatically start

## Bot Commands

### Moderation Commands

- `/mod ban [user] [reason] [delete_days]` - Ban a user from the server
- `/mod kick [user] [reason]` - Kick a user from the server
- `/mod timeout [user] [duration] [reason]` - Timeout a user for a specified duration
- `/mod clear [amount] [user] [contains]` - Clear a specified number of messages

### Global Commands

- `/global profile [user]` - View your or another user's global profile
- `/global collect` - Collect income from all your passive income sources
- `/global leaderboard [category]` - View the global leaderboard
- `/global shop` - View the global shop for passive income items
- `/global buy [item]` - Purchase an item from the global shop
- `/global daily` - Claim your daily reward

## Dashboard Features

- **Inventory Management**: View and manage your inventory items
- **Real-time Income**: Watch your passive income sources generate coins in real-time
- **Income Collection**: Collect income from individual sources or all at once
- **Discord Integration**: Seamless integration with Discord user accounts
- **Achievements**: Track your progress and unlock achievements

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Discord.js for the Discord API integration
- Express for the web server framework
- The Discord community for inspiration and feedback 