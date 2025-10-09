# Apple Music Voice Control - Implementation Plan

## Goal
Control all basic Apple Music app functions using voice commands via Siri.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SIRI VOICE COMMAND                       │
│         "Add this song to my Workout playlist"              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  iOS SHORTCUTS APP                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Simple Commands (Native Shortcuts Actions)          │   │
│  │  - Play/Pause                                        │   │
│  │  - Next/Previous track                               │   │
│  │  - Volume control                                    │   │
│  │  - Play specific playlist/artist/album               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Complex Commands (Shortcut → Webhook)               │   │
│  │  - Add to specific playlist                          │   │
│  │  - Get current track info                            │   │
│  │  - Create new playlist                               │   │
│  │  - Search and play                                   │   │
│  └────────────────┬─────────────────────────────────────┘   │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    │ HTTP POST
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              FLASK WEBHOOK SERVER (py_home)                 │
│              POST /music/<action>                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           APPLE MUSIC HANDLER (services/apple_music.py)     │
│           - Track state/history                             │
│           - Playlist management                             │
│           - Integration with automations                    │
└─────────────────────────────────────────────────────────────┘
```

## Two-Tier Approach

### Tier 1: Native iOS Shortcuts (No Server)
**Direct Siri → Shortcuts → Apple Music**

These work offline, instant response:

| Command | iOS Shortcut Actions |
|---------|---------------------|
| "Play music" | Play Music action |
| "Pause music" | Pause Music action |
| "Next song" | Skip Forward action |
| "Previous song" | Skip Back action |
| "Volume up/down" | Set Volume action |
| "Shuffle on/off" | Set Shuffle action |
| "Repeat on/off" | Set Repeat action |
| "Play [playlist]" | Play Music → Playlist → [name] |
| "Play [artist]" | Play Music → Artist → [name] |
| "Like this song" | Add Music to Library + Love Song |

**Pros:**
- ✅ Works offline
- ✅ Instant response
- ✅ No server needed
- ✅ Native iOS integration

**Cons:**
- ❌ Limited logic/branching
- ❌ Can't track history
- ❌ Can't integrate with home automation

### Tier 2: Webhook-Enhanced (Server-Backed)
**Siri → Shortcuts → py_home server → Response**

These enable complex operations:

| Command | Workflow |
|---------|----------|
| "Add to Workout" | Shortcut gets current track → POST /music/add-to-playlist → Server adds to playlist → Response |
| "What's playing?" | Shortcut gets track info → POST /music/track-info → Server logs/responds → Speak result |
| "Create gym playlist" | Shortcut → POST /music/create-playlist → Server creates → Confirmation |
| "Add and turn on lights" | Shortcut → POST /music/add-and-lights → Server adds to playlist + Tapo control |

**Pros:**
- ✅ Complex logic
- ✅ Track listening history
- ✅ Integrate with home automation
- ✅ Cross-device coordination

**Cons:**
- ❌ Requires server connection
- ❌ Slightly slower
- ❌ More setup

## Apple Music Operations to Support

### Playback Control (Tier 1 - Native)
```
✓ Play/Pause
✓ Next track
✓ Previous track
✓ Seek forward/backward
✓ Volume control (0-100%)
✓ Shuffle on/off
✓ Repeat (off/one/all)
✓ Play specific playlist/album/artist
```

### Library Management (Tier 2 - Server)
```
✓ Add current track to library
✓ Remove from library
✓ Love/Unlike track
✓ Add to specific playlist
✓ Remove from playlist
✓ Create new playlist
```

### Discovery & Search (Tier 1 - Native)
```
✓ Search and play "song name"
✓ Play artist radio
✓ Play genre station
✓ Play recommendations
```

### Information (Tier 2 - Server)
```
✓ Get current track info (title, artist, album)
✓ Get queue/up next
✓ Listening history
```

### Advanced Automations (Tier 2 - Server)
```
✓ "Add to Workout and set lights to red"
✓ "Play Chill playlist and dim lights"
✓ "Save current playlist as snapshot"
✓ Track listening patterns (time of day, genre preferences)
```

## iOS Shortcuts Implementation

### Simple Shortcut: "Next Song"
```
1. Skip Forward
2. [Done]
```

### Simple Shortcut: "Play Workout Playlist"
```
1. Play Music
   - Source: Playlist
   - Name: "Workout"
2. [Done]
```

### Advanced Shortcut: "Add to Workout"
```
1. Get Current Song
2. Get Details of Music (Artist, Title, Album)
3. Text: Combine into JSON
   {
     "artist": [Artist],
     "title": [Title],
     "album": [Album]
   }
4. Get Contents of URL
   - URL: http://raspberrypi.local:5000/music/add-to-playlist
   - Method: POST
   - Request Body: JSON (from step 3)
   - Headers: {"playlist": "Workout"}
5. Show Notification
   - Title: "Added to Workout"
   - Body: "[Title] by [Artist]"
```

### Advanced Shortcut: "What's Playing?"
```
1. Get Current Song
2. Get Details of Music
3. Speak Text
   - "Now playing [Title] by [Artist] from [Album]"
```

### Advanced Shortcut: "Music & Lights for Gym"
```
1. Play Music → Playlist → "Workout"
2. Set Volume → 80%
3. Get Contents of URL
   - URL: http://raspberrypi.local:5000/automation/gym-mode
   - Method: POST
4. Show Notification → "Gym mode activated!"
```

## Server Implementation

### Flask Endpoints (server/app.py)

```python
@app.route('/music/add-to-playlist', methods=['POST'])
def add_to_playlist():
    """
    Add track to specified playlist

    Request:
    {
        "artist": "Taylor Swift",
        "title": "Shake It Off",
        "album": "1989"
    }
    Headers:
    {
        "playlist": "Workout"
    }

    Response:
    {
        "status": "ok",
        "message": "Added 'Shake It Off' to Workout"
    }
    """
    track_info = request.json
    playlist = request.headers.get('playlist', 'default')

    # Log to history
    music_handler.log_track(track_info, action='add_to_playlist', playlist=playlist)

    return jsonify({
        'status': 'ok',
        'message': f"Added '{track_info['title']}' to {playlist}"
    })


@app.route('/music/track-info', methods=['POST'])
def track_info():
    """
    Log current track and return info

    Request:
    {
        "artist": "...",
        "title": "...",
        "album": "...",
        "duration": 245,
        "timestamp": "2025-10-08T14:30:00Z"
    }

    Response:
    {
        "status": "ok",
        "track": {...},
        "recommendations": ["Similar track 1", "Similar track 2"]
    }
    """
    track_info = request.json

    # Log listening history
    music_handler.log_track(track_info, action='now_playing')

    # Could add: recommendations, mood detection, etc.

    return jsonify({
        'status': 'ok',
        'track': track_info
    })


@app.route('/music/create-playlist', methods=['POST'])
def create_playlist():
    """
    Create new playlist (logs intent, actual creation in iOS)

    Request:
    {
        "name": "Road Trip 2025",
        "description": "Summer road trip vibes"
    }
    """
    playlist_info = request.json

    # Log playlist creation
    music_handler.log_playlist_creation(playlist_info)

    return jsonify({
        'status': 'ok',
        'message': f"Playlist '{playlist_info['name']}' created"
    })


@app.route('/automation/music-and-lights', methods=['POST'])
def music_and_lights():
    """
    Coordinate music with home automation

    Request:
    {
        "scene": "gym",  // gym, chill, party, focus
        "playlist": "Workout",
        "volume": 80
    }
    """
    scene = request.json.get('scene', 'default')

    if scene == 'gym':
        # Turn on specific lights, set colors
        from components.tapo import turn_on
        turn_on("Heater")  # Or specific gym lights

    elif scene == 'chill':
        # Dim lights
        pass

    elif scene == 'party':
        # Colorful lights
        pass

    return jsonify({'status': 'ok', 'scene': scene})
```

### Music Handler (services/apple_music.py)

```python
"""
Apple Music integration and history tracking

Stores:
- Listening history (what, when, duration)
- Playlist management logs
- Music preferences/patterns
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

class AppleMusicHandler:
    def __init__(self, history_file='data/music_history.json'):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(exist_ok=True)

        # Load existing history
        if self.history_file.exists():
            with open(self.history_file) as f:
                self.history = json.load(f)
        else:
            self.history = {
                'tracks': [],
                'playlists': {},
                'preferences': {}
            }

    def log_track(self, track_info, action='now_playing', playlist=None):
        """
        Log track play/add event

        Args:
            track_info: {artist, title, album, duration, ...}
            action: 'now_playing', 'add_to_playlist', 'loved', etc.
            playlist: Playlist name if adding to playlist
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'track': track_info
        }

        if playlist:
            entry['playlist'] = playlist

        self.history['tracks'].append(entry)
        self._save()

        kvlog(logger, logging.INFO, service='apple_music', action=action,
              artist=track_info['artist'], title=track_info['title'],
              playlist=playlist or 'none')

    def log_playlist_creation(self, playlist_info):
        """Log playlist creation"""
        playlist_name = playlist_info['name']
        self.history['playlists'][playlist_name] = {
            'created': datetime.now().isoformat(),
            'info': playlist_info
        }
        self._save()

        kvlog(logger, logging.INFO, service='apple_music', action='create_playlist',
              name=playlist_name)

    def get_listening_history(self, limit=50):
        """Get recent listening history"""
        return self.history['tracks'][-limit:]

    def get_top_artists(self, limit=10):
        """Get most played artists"""
        from collections import Counter
        artists = [t['track']['artist'] for t in self.history['tracks']]
        return Counter(artists).most_common(limit)

    def _save(self):
        """Save history to disk"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
```

## Voice Commands to Support

### Basic Playback
```
"Play music"
"Pause music"
"Next song"
"Previous song"
"Volume 50" / "Volume up" / "Volume down"
"Shuffle on"
"Repeat all"
```

### Playlist Control
```
"Play Workout playlist"
"Play Chill Out"
"Add this to Workout"
"Add to my favorites"
"Create a new playlist called Road Trip"
```

### Discovery
```
"Play Taylor Swift"
"Play 1989 album"
"Play indie rock"
"Play something chill"
```

### Information
```
"What's playing?"
"Who sings this?"
"What album is this from?"
```

### Integrated Automation
```
"Gym mode" (plays Workout + turns on lights)
"Chill vibes" (plays Chill playlist + dims lights)
"Party time" (plays Party playlist + colorful lights)
"Focus mode" (plays Focus playlist + turns off distractions)
```

## Implementation Phases

### Phase 1: Native Shortcuts (No Server)
**Time: 1-2 hours**
1. Create 10-15 basic iOS Shortcuts
2. Assign Siri phrases
3. Test all basic operations

**Shortcuts to Create:**
- Play/Pause/Next/Previous
- Play [Workout/Chill/Party/Focus] playlist
- Volume [0-100]
- Shuffle/Repeat toggle
- "What's playing?" (speak current track)
- Add to library
- Love song

### Phase 2: Server Endpoints
**Time: 2-3 hours**
1. Add `/music/*` endpoints to Flask server
2. Create `services/apple_music.py` handler
3. Create `data/music_history.json` storage
4. Add structured logging

**Endpoints:**
- POST `/music/add-to-playlist`
- POST `/music/track-info`
- POST `/music/create-playlist`
- GET `/music/history`
- GET `/music/stats`

### Phase 3: Advanced Shortcuts
**Time: 1 hour**
1. Create webhook-based shortcuts
2. Test server integration
3. Add error handling

**Shortcuts:**
- "Add to [Playlist]" (with confirmation)
- "What's playing?" (with server logging)
- "Show my top artists"
- "Create [Name] playlist"

### Phase 4: Automation Integration
**Time: 1-2 hours**
1. Create scene-based endpoints
2. Integrate with existing home automation
3. Test coordinated operations

**Automations:**
- Gym mode (music + lights + climate)
- Chill mode (music + lights + temp)
- Party mode (music + lights)
- Focus mode (music + DND + lights)
- Bedtime (music fade + lights off + sleep temp)

## Data Storage

### music_history.json
```json
{
  "tracks": [
    {
      "timestamp": "2025-10-08T14:30:00Z",
      "action": "add_to_playlist",
      "playlist": "Workout",
      "track": {
        "artist": "Taylor Swift",
        "title": "Shake It Off",
        "album": "1989",
        "duration": 219
      }
    }
  ],
  "playlists": {
    "Workout": {
      "created": "2025-10-01T10:00:00Z",
      "info": {
        "name": "Workout",
        "description": "High energy gym music"
      }
    }
  },
  "preferences": {
    "favorite_genres": ["pop", "rock", "electronic"],
    "workout_tempo": "high-energy",
    "chill_artists": ["Bon Iver", "Iron & Wine"]
  }
}
```

## iOS Shortcuts Guide

### Creating a Basic Shortcut

1. Open **Shortcuts** app
2. Tap **+** (New Shortcut)
3. Add actions:
   - Search "Play Music"
   - Configure (playlist, artist, etc.)
4. Tap **⋯** → Rename → "Play Workout"
5. Tap **Add to Siri**
6. Record phrase: "Start my workout"

### Creating a Webhook Shortcut

1. Open **Shortcuts** app
2. Tap **+**
3. Add actions:
   - "Get Current Song"
   - "Get Details of Music"
   - "Get Contents of URL"
     - URL: `http://raspberrypi.local:5000/music/add-to-playlist`
     - Method: POST
     - Headers: `{"playlist": "Workout"}`
     - Body: JSON with song details
   - "Show Notification"
4. Name: "Add to Workout"
5. Add to Siri: "Add this to my workout"

## Benefits

### Offline Native Commands
- Play/pause/skip work without internet
- Instant response
- No server dependency

### Server-Enhanced Features
- Track listening history
- Smart recommendations
- Cross-device automation
- Complex playlist management
- Integration with home scenes

### Home Automation Integration
- Music-triggered lighting
- Mood-based climate control
- Time-of-day recommendations
- Activity detection (gym, focus, chill)

## Future Enhancements

### Smart Features
- Auto-create workout playlists based on tempo
- Mood detection from listening patterns
- Time-based recommendations
- Weather-based music selection

### Cross-Platform
- Sync with Spotify/YouTube Music
- Multi-room audio control
- Speaker group management

### Advanced Automation
- "Arrive home" → Resume music from car
- "Leaving home" → Pause music
- "Bedtime" → Gradual fade out
- "Morning" → Gentle wake-up playlist

## Testing Plan

1. **Native shortcuts** - Test each basic command
2. **Webhook shortcuts** - Test server communication
3. **Error handling** - Test offline scenarios
4. **Automation integration** - Test music + lights coordination
5. **History tracking** - Verify data logging
6. **Voice phrase testing** - Ensure Siri recognition

## Notes

- iOS Shortcuts has direct access to Apple Music API (no external API needed)
- Server is optional for basic use, required for history/automation
- All music control stays on device for privacy
- Server only logs metadata (artist/title), not playback data
- Works offline for Tier 1 commands

## Success Criteria

- [ ] 15+ voice commands working
- [ ] Can control playback without touching phone
- [ ] Can add songs to playlists by voice
- [ ] Listening history tracked
- [ ] Music integrated with 3+ home automations
- [ ] All commands work reliably
