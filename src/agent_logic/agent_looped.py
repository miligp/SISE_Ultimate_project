import asyncio
from typing import List
from pydantic_ai.messages import ModelMessage

# Import de l'instance de l'agent définie dans pydantic_ai_agent.py
from src.agent_logic.pydantic_ai_agent import agent 

async def chat_loop() -> None:
    """Exécute une boucle conversationnelle interactive avec l'agent."""
    message_history: List[ModelMessage] = []
    
    print("Agent copilote initialisé. (Tapez 'exit' pour quitter)")
    
    while True:
        try:
            user_input: str = input("\n>>> ")
            if user_input.lower().strip() in ["exit", "quit", "q"]:
                break
            
            if not user_input.strip():
                continue

            # Injection de l'historique dans le contexte de l'agent
            result = await agent.run(user_input, message_history=message_history)
            
            # Mise à jour de l'état avec la nouvelle séquence (requête, appels d'outils, réponse)
            message_history.extend(result.new_messages())
            
            # Affichage de la réponse (utiliser result.output ou result.data selon la version de pydantic-ai)
            print(f"\n<<< {result.output}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERREUR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(chat_loop())