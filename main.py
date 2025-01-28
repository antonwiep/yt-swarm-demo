from swarm import Swarm, Agent
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

client = Swarm()

def transfer_to_research_agent():
    return research_agent

def transfer_to_copy_agent():
    return copy_agent

def transfer_to_review_agent():
    return review_agent

def transfer_to_finalization_agent():
    return finalization_agent

def save_campaign_to_file(job_title: str, campaign_content: str):

    os.makedirs("work", exist_ok=True)
    
    filename = f"work/{job_title.lower().replace(' ', '_')}_recruiting_ad.txt"
    with open(filename, 'w') as f:
        f.write(campaign_content)
    return f"Recruiting-Ad saved to {filename}"

def scrape_website(url: str) -> str:
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:8000] 
        
    except Exception as e:
        return f"Error scraping website: {str(e)}"

coordinator_agent = Agent(
    name="Kampagnen-Koordinator",
    instructions="""Du bist der Einstieg in den Recruiting-Ad-Prozess.
    1. Frage den User nach dem Link zur Stellenausschreibung / Karriereseite (falls noch nicht erhalten).
    2. Sobald du den Link hast, frage ob es besondere Benefits oder Anforderungen gibt die nicht fehlen dürfen.
    3. Leite dann SOFORT an Recruiting-Research-Agent weiter mit transfer_to_research_agent().""",
    functions=[transfer_to_research_agent]
)

research_agent = Agent(
    name="Research-Spezialist",
    instructions="""Du bist unser Research-Spezialist für Recruiting-Ads-Kampagnen.
    Deine Aufgabe ist es, die gesuchte Stellenausschreibung des Kunden zu analysieren und:
    1. Nutze scrape_website() mit der vom Koordinator erhaltenen Stellenausschreibungs-URL.
    2. Extrahiere: Jobtitel, Standort, Firmenname, Benefits, Anforderungen, Bewerbungslink, etc.
    3. Ergänze alle zusätzlich vom Koordinator erhaltenen Informationen (z.B. spezielle Benefits).
    4. Prüfe gegen unsere Master-Checkliste:
       - Jobtitel
       - Standort
       - Firmenname
       - Benefits (inkl. zusätzlicher Informationen)
       - Anforderungen
    5. Wenn etwas fehlt, frage gezielt nach.
    6. Gib eine strukturierte Zusammenfassung aus:
       === JOB-TITEL ===
       ...
       === STANDORT ===
       ...
       === FIRMA ===
       ...
       === BENEFITS ===
       ... (inkl. aller zusätzlichen Informationen)
       === ANFORDERUNGEN ===
       ...
    3. Nach der Analyse SOFORT zum Copy-Agent weiterleiten mit transfer_to_copy_agent()""",
    functions=[scrape_website, transfer_to_copy_agent]
)

copy_agent = Agent(
    name="Copy-Spezialist",
    instructions="""Du bist unser Facebook-Ads-Texter.
    Dein Workflow:
    1. Du schreibst exakt EINE Social-Recruiting-Anzeige.
        Halte dich an folgendes Muster:
        
        - Hook-Zeile mit Emojis:
        z.B. 👨‍🔧 Elektroniker (m/w/d) aus [Standort] gesucht?
        - Kurzer Problem-/Spannungsaufbau:
        z.B. 'Genervt von unbezahlten Überstunden...'
        - Firmenvorstellung in 1–2 Sätzen
        - Bullets mit Benefits (mind. 3, max. 10), jede mit Emoji
        - Kurze Anforderungen:
        z.B. 'Was musst Du mitbringen? Ausbildung XY...'
        - Finaler Call-to-Action mit "Jetzt Bewerben [Link einfügen]"
    2. SOFORT zum Review-Agent mit transfer_to_review_agent() weiterleiten""",
    functions=[transfer_to_review_agent]
)

review_agent = Agent(
    name="Review-Spezialist",
    instructions="""Du bist unser Facebook-Ads-Prüfer.
    Dein Workflow:
    1. Du überprüfst die vom AdCopy-Agent generierte Recruiting-Ad auf folgende Kriterien:
        - Gibt es eine Hook-Zeile mit Emojis?
        - Wird eine Problem-/Frage formuliert?
        - Kommt eine Firmenvorstellung in 1-2 Sätzen vor?
        - Gibt es mind. 3 Benefits in Bullet-Point-Form (mit Emojis)?
        - Werden die Anforderungen kurz erwähnt?
        - Gibt es eine klare CTA mit Link?
    2. MAXIMAL 2-3 konkrete Verbesserungsvorschläge machen
    3. SOFORT zum Finalisierungs-Agent weiterleiten mit transfer_to_finalization_agent()""",
    functions=[transfer_to_finalization_agent]
)

finalization_agent = Agent(
    name="Finalisierungs-Spezialist",
    instructions="""Du bist der letzte Spezialist im Prozess.
    Dein Workflow:
    1. Nimm das Review-Feedback.
    2. Überarbeite die Ad minimal, damit sie alle Kriterien erfüllt.
    3. Speichere das Endergebnis mit save_campaign_to_file().
       Dateiname: z.B. <jobtitel>_recruiting_ad.txt
    
    WICHTIG: 
    - Du MUSST IMMER save_campaign_to_file(job_title, campaign_content) aufrufen
    - Der job_title ist der Jobtitel aus dem Kontext und DARF keine Sonderzeichen wie /, (, ), etc. enthalten, da es als Dateiname verwendet wird
    - campaign_content MUSS die KOMPLETTE Research-Analyse enthalten
    - Kopiere ALLE Analyse-Kategorien aus dem Research-Teil
    - Nach dem Speichern bestätige mit "Kampagne wurde gespeichert".""",
    functions=[save_campaign_to_file]
)

def main():
    print("📢 Willkommen bei deinem Social Recruiting Kampagnen-Creator!")
    print("Gib eine Stellenanzeigen URL ein.")
    print("Tippe 'exit' zum Beenden.")
    
    conversation_history = []
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            print("Peace out...")
            break
        
        conversation_history.append({"role": "user", "content": user_input})
            
        response = client.run(
            agent=coordinator_agent,
            messages=conversation_history, 
            stream=True
        )
        
        print("\nAssistant: ", end="")
        for chunk in response:
            if "content" in chunk and chunk["content"]:
                print(chunk["content"], end="", flush=True)
            elif "function_call" in chunk or "delim" in chunk or "response" in chunk:
                continue
        print()
        
        if hasattr(response, 'messages'):
            last_message = next((msg for msg in reversed(response.messages) 
                               if msg["role"] == "assistant"), None)
            if last_message:
                conversation_history.append(last_message)

if __name__ == "__main__":
    main()
