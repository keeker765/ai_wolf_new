# AI Werewolf Backend

This is the FastAPI backend for the AI Werewolf game.

## Features

- ✅ Room management (create, join, leave, start)
- ✅ WebSocket real-time communication
- ✅ Complete game state machine (Init → Night → Day → Vote → Resolve → End)
- ✅ Role assignment (Werewolf, Seer, Witch, Hunter, Villager)
- ✅ Night actions (wolf kill, witch heal/poison, seer check)
- ✅ Voting system with tie-breaking and revote logic
- ✅ AI speech generation and action decisions (OpenAI integration)
- ✅ Replay system (event timeline, game summary)
- ✅ Authentication (guest and email verification - test mode)
- ✅ Stub endpoints for STT, billing, voice token

## Requirements

- Python 3.11+
- FastAPI
- Redis (optional, for production)
- PostgreSQL (optional, for production)

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

3. Set your OpenAI API key (optional, will use fallback if not set):

```bash
# In .env file
OPENAI_API_KEY=sk-your-api-key-here
```

## Running the Server

### Development Mode

```bash
uvicorn app.main:app --reload
```

The server will be available at `http://localhost:8000`.

### API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with pytest:

```bash
PYTHONPATH=. pytest -q
```

Run with coverage:

```bash
PYTHONPATH=. pytest --cov=app tests/
```

## Code Quality

Format code:

```bash
black .
```

Lint code:

```bash
ruff check .
```

Auto-fix linting issues:

```bash
ruff check --fix .
```

Type check:

```bash
mypy app tests
```

## Project Structure

```
backend/
├── app/
│   ├── core/              # Core utilities (errors, middleware)
│   ├── routers/           # API route handlers
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── rooms.py       # Room management
│   │   ├── games.py       # Game actions and WebSocket
│   │   ├── ai.py          # AI service endpoints
│   │   ├── replay.py      # Replay system
│   │   ├── stt.py         # Speech-to-text stub
│   │   ├── billing.py     # Billing stub
│   │   └── stats.py       # Statistics
│   ├── services/          # Business logic
│   │   ├── game_state.py  # Game state machine
│   │   ├── game_actions.py # Game action handlers
│   │   ├── ai_service.py  # AI integration
│   │   ├── room_manager.py # Room management
│   │   └── vote.py        # Voting logic
│   └── main.py            # FastAPI application
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

## API Endpoints

### Authentication

- `POST /auth/guest` - Create guest account
- `POST /auth/email/request` - Request email verification code
- `POST /auth/email/verify` - Verify email code

### Rooms

- `GET /rooms` - List all rooms
- `POST /rooms` - Create a room
- `GET /rooms/{room_id}` - Get room details
- `POST /rooms/{room_id}/join` - Join a room
- `POST /rooms/{room_id}/leave` - Leave a room
- `POST /rooms/{room_id}/start` - Start a game

### Games

- `GET /games/{game_id}` - Get game state
- `POST /games/{game_id}/action` - Submit action (chat, vote, skill)
- `POST /games/{game_id}/advance` - Advance to next phase (admin/testing)
- `WS /games/ws/{room_id}` - WebSocket for real-time updates

### AI

- `POST /ai/generate_speech` - Generate AI speech
- `POST /ai/decide_action` - AI action decision

### Replay

- `GET /replay/{game_id}/timeline` - Get event timeline
- `GET /replay/{game_id}/summary` - Get game summary

### Other

- `GET /healthz` - Health check
- `GET /stats/rooms` - Room statistics
- `GET /billing/products` - Billing products (stub)
- `POST /billing/purchase` - Purchase (stub)
- `POST /stt/transcribe` - Transcribe audio (stub)

## WebSocket Protocol

Connect to `/games/ws/{room_id}` with optional JWT token.

### Client → Server Messages

```json
{"type": "ping"}
{"type": "chat_message", "text": "Hello"}
{"type": "ack", "seq": 123}
```

### Server → Client Messages

```json
{"type": "pong"}
{"type": "state_update", "phase": "Night", "round": 1, "alive_players": [1,2,3]}
{"type": "chat_message", "from": "player_1", "text": "Hello"}
{"type": "vote_event", "seat": 1, "target": 2}
{"type": "day_deaths_announced", "deaths": [3]}
{"type": "game_ended", "winner": "villagers"}
```

## Game Flow

1. **Room Creation**: Host creates a room with seat count (6/9/10)
2. **Players Join**: Players join and select seats
3. **Game Start**: Host starts the game, roles are assigned
4. **Night Phase**: Werewolves choose kill, Witch can heal/poison, Seer checks
5. **Day Phase**: Deaths announced, players discuss
6. **Vote Phase**: Players vote to lynch
7. **Resolve Phase**: Process results, check victory
8. **Loop**: Return to Night if game continues
9. **End**: Game ends when villagers or werewolves win

## Configuration

Key environment variables (see `.env.example`):

- `OPENAI_API_KEY` - OpenAI API key for AI features
- `OPENAI_MODEL` - Model to use (default: gpt-4o-mini)
- `JWT_SECRET` - Secret for JWT tokens
- `CORS_ORIGINS` - Allowed CORS origins
- `DATABASE_URL` - PostgreSQL connection (for production)
- `REDIS_URL` - Redis connection (for production)

## Development Notes

### Test Mode Features

- Email verification codes are only logged, not sent
- In-memory storage for rooms, games, and replay (no persistence)
- Stub user authentication (no real JWT validation yet)
- AI fallback responses when OpenAI is not configured

### Production Checklist

- [ ] Set up PostgreSQL database
- [ ] Set up Redis for state and pub/sub
- [ ] Implement proper JWT authentication
- [ ] Add rate limiting
- [ ] Set up monitoring and logging
- [ ] Configure CORS properly
- [ ] Set up SSL/TLS
- [ ] Add database migrations (Alembic)
- [ ] Implement replay data cleanup (30-day retention)

## License

MIT
