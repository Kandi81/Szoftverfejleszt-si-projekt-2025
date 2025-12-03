# \## Architecture (v0.4.0+)

# 

# Sortify now uses a modular architecture for better maintainability:

# 

# sortify/

# ├── main.py # Entry point (NEW)

# ├── sortifyui.py # Legacy UI (to be refactored)

# ├── utils/ # Utility functions

# │ ├── resource\_utils.py

# │ ├── date\_utils.py

# │ └── html\_utils.py

# ├── models/ # Data models

# │ ├── email\_model.py

# │ └── app\_state.py

# ├── services/ # Service layer

# │ ├── gmail\_service.py

# │ ├── storage\_service.py

# │ ├── gemini\_service.py

# │ ├── perplexity\_service.py

# │ ├── verification\_service.py

# │ └── ai\_factory.py

# ├── business/ # Business logic

# │ └── rules\_engine.py

# └── controllers/ # Controllers

# ├── email\_controller.py

# ├── ai\_controller.py

# └── auth\_controller.py







\### Running the application



New modular entry point

python main.py



Legacy entry point (still works)

python sortifyui.py

undefined

