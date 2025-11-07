# AI Werewolf Game (狼人杀 AI 版)

An AI-powered Werewolf (Mafia) game with a Flutter web client and FastAPI backend. Play with AI opponents powered by OpenAI, or challenge your friends in real-time multiplayer matches.

## Project Status

✅ **Backend**: Fully implemented and tested
- Complete game state machine (Init → Night → Day → Vote → Resolve → End)
- WebSocket real-time communication
- OpenAI integration for AI players
- Room and game management
- Replay system

🚧 **Frontend**: Planned (Flutter Web)
- See `docs/frontend-guidelines-and-plan.md` for specifications

## Features

### Current (Backend)

- 🎮 **Full Game Logic**: Complete implementation of Werewolf game rules
- 🤖 **AI Players**: OpenAI-powered speech generation and decision making
- 🔄 **Real-time Updates**: WebSocket communication for live game events
- 👥 **Room Management**: Create, join, and manage game rooms
- 📊 **Replay System**: Review past games with event timelines
- 🔐 **Authentication**: Guest and email verification (test mode)
- 🧪 **Well Tested**: Comprehensive test suite with 26+ tests

### Planned

- 🎨 **Flutter Web UI**: Modern, responsive game interface
- 🎤 **Voice Chat**: Real-time voice communication (Agora/WebRTC)
- 🎙️ **Speech-to-Text**: AI analysis of voice input
- 💰 **Monetization**: In-app purchases and premium features

## Quick Start

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY (optional)

# Run server
uvicorn app.main:app --reload

# Visit http://localhost:8000/docs for API documentation
```

### Testing

```bash
cd backend

# Run tests
PYTHONPATH=. pytest -q

# Run linting
ruff check .
black --check .

# Type checking
mypy app tests
```

## Architecture

### Backend (FastAPI)

- **Framework**: FastAPI (async Python)
- **WebSocket**: Real-time communication
- **AI**: OpenAI API integration
- **Storage**: In-memory (test), PostgreSQL + Redis (production)

### Frontend (Flutter)

- **Framework**: Flutter Web
- **State Management**: Riverpod
- **Communication**: HTTP + WebSocket
- **UI**: Material Design 3

## Game Rules

- **Roles**: Werewolf, Seer, Witch, Hunter, Villager
- **Seats**: 6, 9, or 10 players
- **Phases**: Night (actions) → Day (discussion) → Vote (lynch) → Resolve
- **Victory**: Villagers win if all werewolves eliminated; werewolves win if they equal/outnumber villagers

See `docs/game-logic.md` for detailed rules.

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:

- `POST /auth/guest` - Create guest account
- `POST /rooms` - Create a room
- `POST /rooms/{id}/start` - Start a game
- `WS /games/ws/{room_id}` - WebSocket connection
- `POST /ai/generate_speech` - AI speech generation
- `GET /replay/{game_id}/timeline` - Game replay

## Development

### Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── app/           # Application code
│   │   ├── core/      # Core utilities
│   │   ├── routers/   # API endpoints
│   │   └── services/  # Business logic
│   └── tests/         # Test suite
├── docs/              # Documentation
│   ├── api-spec.md    # API specification
│   ├── game-logic.md  # Game rules
│   └── dev-plan.md    # Development plan
└── .github/           # CI/CD workflows
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Code Quality

All code must pass:

- ✅ Ruff (linting)
- ✅ Black (formatting)
- ✅ Mypy (type checking)
- ✅ Pytest (unit tests)

## Documentation

- [API Specification](docs/api-spec.md)
- [Game Logic](docs/game-logic.md)
- [Development Plan](docs/dev-plan.md)
- [Frontend Guidelines](docs/frontend-guidelines-and-plan.md)
- [Sample Game Log](docs/sample-game-log.md)
- [Backend README](backend/README.md)

## Roadmap

### Phase 1: Backend (✅ Complete)

- [x] Project structure and dependencies
- [x] Authentication system
- [x] Room management
- [x] Game state machine
- [x] WebSocket communication
- [x] AI integration
- [x] Replay system
- [x] Tests and documentation

### Phase 2: Frontend (🚧 Planned)

- [ ] Flutter project setup
- [ ] Authentication UI
- [ ] Room lobby
- [ ] Game interface
- [ ] WebSocket integration
- [ ] Replay viewer

### Phase 3: Polish (📋 Future)

- [ ] Voice chat integration
- [ ] Speech-to-text
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Production deployment

### Phase 4: Monetization (💡 Ideas)

- [ ] Premium features
- [ ] Cosmetic items
- [ ] Advanced AI opponents
- [ ] Tournament system

## Environment Variables

Key configuration (see `backend/.env.example`):

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Security
JWT_SECRET=your-secret-key

# Database (production)
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
```

## Testing

```bash
# Backend tests
cd backend
PYTHONPATH=. pytest -v

# With coverage
PYTHONPATH=. pytest --cov=app tests/

# Specific test
PYTHONPATH=. pytest tests/test_game_logic.py -v
```

## Deployment

### Development

```bash
cd backend
uvicorn app.main:app --reload
```

### Production

```bash
# Docker
docker build -t ai-werewolf-backend .
docker run -p 8000:8000 ai-werewolf-backend

# Or use docker-compose (planned)
docker-compose up
```

## License

MIT

## Credits

- Game Design: Based on classic Werewolf/Mafia rules
- AI: Powered by OpenAI
- Framework: FastAPI, Flutter

## Support

For issues and questions:

- Open an issue on GitHub
- Check the documentation in `docs/`
- Review the API docs at `/docs` endpoint

---

**Status**: Backend complete and ready for frontend development! 🎉
