"""Entry point: genera un episodio completo del podcast."""

from dotenv import load_dotenv
load_dotenv()

from src.pipeline import run

if __name__ == "__main__":
    episode = run()
    print(f"\nEpisodio pronto: {episode}")
