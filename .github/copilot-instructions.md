# Development Guidelines

## About this application
This application is a Texas No Limit Holdem poker game with a GUI.
It is built using Python and Pygame and other libraries.
The game supports multiple players, betting rounds, and hand evaluations.
It should also have logic for the computer players to make decisions based on their hand strength and the game state.

## AI Assistance Best Practices
- Explain how the problem will be solved and why that method is chosen.
- Always run tests after AI-generated changes, preferably after each modification.
- Specify the exact file when requesting modifications.
- Keep generated methods short, focused, and modular.
- Ask for explanations of complex game logic before implementing.
- Suggest unit tests for new or modified functionality and run them together with existing tests.
- Code that is never used should be removed.
- Separate game logic, GUI code, and AI logic into distinct modules.
- For GUI (Pygame) code, keep the event loop, rendering, and game state updates clearly separated.
- Add concise inline comments for non-obvious or complex logic.
- Validate all user input and handle edge cases.
- Use concise, meaningful commit messages and update changelogs for significant changes.
- Document any new third-party dependencies and update requirements.txt as needed.
- Use static analysis tools (e.g., mypy, pylint) and address reported issues.
- Ensure all new or changed code is covered by unit tests and report test coverage.
- Suggest refactoring or code simplification opportunities when appropriate.
- Comments should be clear and concise, avoiding redundancy with the code itself. 
- Do not state the obvious or elaborate unnecessarily.
