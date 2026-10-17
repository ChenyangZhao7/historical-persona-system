"""
Bulk import historical figures into the database.
Run from the backend directory with the venv activated:
    python bulk_import.py

Requires ANTHROPIC_API_KEY to be set and backend running on port 8000.
Each figure takes ~5-10s (one Claude API call). 500 figures ≈ 50-80 minutes.
Already-imported figures are skipped automatically.
"""

import requests
import time
import sys

API = "http://localhost:8000"

FIGURES = [
    # ── Ancient Egypt ──────────────────────────────────────────────
    "Hammurabi", "Ramesses II", "Thutmose III", "Hatshepsut", "Akhenaten",
    "Cleopatra VII", "Nefertiti", "Tutankhamun", "Amenhotep III", "Seti I",
    "Thutmose I", "Amenhotep I", "Ramesses III", "Ptolemy III Euergetes", "Ptolemy II Philadelphus",

    # ── Ancient Mesopotamia & Near East ────────────────────────────
    "Cyrus the Great", "Darius I", "Xerxes I", "Cambyses II", "Artaxerxes I",
    "Ashurbanipal", "Tiglath-Pileser III", "Sargon of Akkad", "Nebuchadnezzar II",
    "Sennacherib", "Esarhaddon", "Naram-Sin", "Ur-Nammu",

    # ── Ancient Greece ──────────────────────────────────────────────
    "Homer", "Hesiod", "Sappho", "Pindar", "Herodotus",
    "Thucydides", "Sophocles", "Euripides", "Aristophanes", "Aeschylus",
    "Socrates", "Plato", "Aristotle", "Diogenes", "Epicurus",
    "Pythagoras", "Archimedes", "Euclid", "Hippocrates", "Galen",
    "Pericles", "Themistocles", "Leonidas I", "Alcibiades", "Demosthenes",
    "Philip II of Macedon", "Alexander the Great", "Ptolemy I Soter", "Seleucus I Nicator", "Pyrrhus of Epirus",
    "Solon", "Cleisthenes", "Miltiades", "Xenophon", "Plutarch",
    "Theophrastus", "Eratosthenes", "Aristarchus of Samos", "Hypatia", "Plotinus",

    # ── Ancient Rome ────────────────────────────────────────────────
    "Hannibal", "Scipio Africanus", "Julius Caesar", "Pompey", "Mark Antony",
    "Cicero", "Cato the Younger", "Brutus", "Octavian Augustus", "Tiberius",
    "Caligula", "Claudius", "Nero", "Vespasian", "Trajan",
    "Hadrian", "Marcus Aurelius", "Commodus", "Diocletian", "Constantine the Great",
    "Sulla", "Marius", "Crassus", "Spartacus", "Vercingetorix",
    "Seneca the Younger", "Ovid", "Virgil", "Tacitus", "Livy",
    "Julian the Apostate", "Theodosius I", "Attila the Hun", "Alaric I", "Odoacer",

    # ── Ancient China ───────────────────────────────────────────────
    "Confucius", "Mencius", "Laozi", "Zhuangzi", "Mozi",
    "Qin Shi Huang", "Han Gaozu", "Han Wudi", "Wang Mang", "Cao Cao",
    "Liu Bei", "Sun Quan", "Zhuge Liang", "Sima Yi", "Guan Yu",
    "Sun Tzu", "Shang Yang", "Li Si", "Zhang Liang", "Han Xin",
    "Emperor Yao", "Emperor Shun", "King Wen of Zhou", "Duke of Zhou", "Guan Zhong",

    # ── Ancient India ───────────────────────────────────────────────
    "Siddhartha Gautama", "Ashoka", "Chandragupta Maurya", "Bindusara", "Samudragupta",
    "Chandragupta II", "Harsha", "Kautilya", "Aryabhata", "Kalidasa",
    "Mahavira", "Nagarjuna", "Vasubandhu", "Kumagupta I", "Skandagupta",

    # ── Early Islam ─────────────────────────────────────────────────
    "Muhammad", "Abu Bakr", "Umar ibn al-Khattab", "Ali ibn Abi Talib", "Aisha",
    "Muawiyah I", "Yazid I", "Abd al-Malik ibn Marwan", "Al-Hajjaj ibn Yusuf", "Umar II",
    "Harun al-Rashid", "Al-Mamun", "Al-Mutasim", "Hulagu Khan", "Saladin",

    # ── Medieval Europe ─────────────────────────────────────────────
    "Charlemagne", "Charles Martel", "Pepin the Short", "Louis the Pious", "Alfred the Great",
    "William the Conqueror", "Richard I of England", "John of England", "Edward I of England", "Edward III of England",
    "Joan of Arc", "Eleanor of Aquitaine", "Isabella I of Castile", "Blanche of Castile", "Margaret of Anjou",
    "Vlad the Impaler", "Jan Hus", "William Wallace", "Robert the Bruce", "Owain Glyndwr",
    "Henry V of England", "Henry II of England", "Thomas Becket", "Simon de Montfort", "Wat Tyler",
    "Frederick I Barbarossa", "Frederick II Holy Roman Emperor", "Rudolf I of Germany", "Henry IV Holy Roman Emperor", "Gregory VII",
    "Otto I Holy Roman Emperor", "Louis IX of France", "Philip IV of France", "Charles VII of France", "Charles the Bold",
    "Rodrigo Díaz de Vivar", "Alfonso X of Castile", "James I of Aragon", "Ferdinand III of Castile", "Afonso I of Portugal",

    # ── Medieval Islamic World ──────────────────────────────────────
    "Nur ad-Din", "Baybars", "Suleiman the Magnificent", "Mehmed II",
    "Al-Ghazali", "Ibn Rushd", "Ibn Khaldun", "Avicenna", "Al-Biruni",
    "Al-Kindi", "Omar Khayyam", "Rumi", "Ibn Battuta", "Ibn Tufayl",
    "Al-Idrisi", "Al-Razi", "Al-Farabi", "Al-Masudi", "Al-Tabari",

    # ── Medieval Asia ───────────────────────────────────────────────
    "Genghis Khan", "Ögedei Khan", "Kublai Khan", "Timur", "Babur",
    "Tang Taizong", "Wu Zetian", "Tang Xuanzong", "Song Taizu", "Yue Fei",
    "Zhu Yuanzhang", "Yongle Emperor", "Zheng He", "Wang Anshi", "Su Shi",
    "Taira no Kiyomori", "Minamoto no Yoritomo", "Hojo Tokimune", "Kusunoki Masashige", "Ashikaga Takauji",
    "Sejong the Great", "Wang Geon", "Gwanggaeto the Great", "Yi Sun-sin", "Kim Yusin",

    # ── Pre-Columbian Americas & Africa ────────────────────────────
    "Mansa Musa", "Sundiata Keita", "Pachacuti", "Moctezuma I", "Huayna Capac",
    "Moctezuma II", "Cuauhtémoc", "Atahualpa", "Huascar", "Tupac Yupanqui",
    "Shaka Zulu", "Osei Tutu", "Nzinga of Ndongo", "Idris Alooma", "Yusuf ibn Tashfin",

    # ── Renaissance & Reformation ───────────────────────────────────
    "Leonardo da Vinci", "Michelangelo", "Raphael", "Titian", "Botticelli",
    "Copernicus", "Galileo Galilei", "Johannes Kepler", "Tycho Brahe", "Francis Bacon",
    "Martin Luther", "John Calvin", "Erasmus", "Thomas More", "Ignatius of Loyola",
    "Henry VIII of England", "Elizabeth I of England", "Mary Queen of Scots", "Francis Drake", "Walter Raleigh",
    "Niccolò Machiavelli", "Thomas Cromwell", "Cardinal Wolsey", "Philip Melanchthon", "Huldrych Zwingli",
    "Albrecht Dürer", "Hans Holbein the Younger", "Pieter Bruegel the Elder", "El Greco", "Caravaggio",

    # ── Scientific Revolution & Enlightenment ──────────────────────
    "René Descartes", "Blaise Pascal", "Isaac Newton", "Gottfried Wilhelm Leibniz", "Robert Hooke",
    "Voltaire", "Jean-Jacques Rousseau", "Montesquieu", "Denis Diderot", "Immanuel Kant",
    "John Locke", "Thomas Hobbes", "Baruch Spinoza", "David Hume", "Adam Smith",
    "Robert Boyle", "Antoine Lavoisier", "Carl Linnaeus", "Georges-Louis Leclerc de Buffon", "William Harvey",

    # ── Baroque & Classical Arts ────────────────────────────────────
    "Wolfgang Amadeus Mozart", "Ludwig van Beethoven", "Johann Sebastian Bach", "George Frideric Handel", "Franz Joseph Haydn",
    "Rembrandt van Rijn", "Johannes Vermeer", "Peter Paul Rubens", "Diego Velázquez", "Nicolas Poussin",
    "William Shakespeare", "John Milton", "Miguel de Cervantes", "Molière", "Jean Racine",

    # ── Mughal & Asian Empires ──────────────────────────────────────
    "Akbar the Great", "Shah Jahan", "Aurangzeb", "Shivaji", "Tipu Sultan",
    "Kangxi Emperor", "Qianlong Emperor", "Yongzheng Emperor", "Zhang Juzheng", "Wei Zhongxian",
    "Toyotomi Hideyoshi", "Tokugawa Ieyasu", "Oda Nobunaga", "Date Masamune", "Takeda Shingen",

    # ── Age of Revolutions ──────────────────────────────────────────
    "Peter the Great", "Catherine the Great", "Frederick the Great", "Maria Theresa", "Joseph II",
    "George Washington", "Benjamin Franklin", "Thomas Jefferson", "John Adams", "Alexander Hamilton",
    "Napoleon Bonaparte", "Maximilien Robespierre", "Georges Danton", "Marquis de Lafayette", "Toussaint Louverture",
    "James Madison", "James Monroe", "John Marshall", "Patrick Henry", "Paul Revere",
    "Simón Bolívar", "José de San Martín", "Bernardo O'Higgins", "Antonio López de Santa Anna", "Benito Juárez",
    "Giuseppe Mazzini", "Giuseppe Garibaldi", "Camillo di Cavour", "Victor Emmanuel II", "Louis Kossuth",

    # ── 19th Century ────────────────────────────────────────────────
    "Abraham Lincoln", "Ulysses S. Grant", "William Tecumseh Sherman", "Frederick Douglass", "Harriet Tubman",
    "Charles Darwin", "Michael Faraday", "James Clerk Maxwell", "Louis Pasteur", "Joseph Lister",
    "Karl Marx", "Friedrich Engels", "Mikhail Bakunin", "Peter Kropotkin", "Ferdinand Lassalle",
    "Otto von Bismarck", "Kaiser Wilhelm II", "Franz Joseph I of Austria", "Alexander II of Russia", "Alexander III of Russia",
    "Meiji Emperor", "Saigo Takamori", "Ito Hirobumi", "Fukuzawa Yukichi", "Yamagata Aritomo",
    "Leo Tolstoy", "Fyodor Dostoevsky", "Anton Chekhov", "Ivan Turgenev", "Nikolai Gogol",
    "Charles Dickens", "Victor Hugo", "Honoré de Balzac", "Gustave Flaubert", "Émile Zola",
    "Thomas Edison", "Nikola Tesla", "Louis Daguerre", "Isambard Kingdom Brunel", "George Stephenson",
    "Florence Nightingale", "Elizabeth Cady Stanton", "Susan B. Anthony", "Sojourner Truth", "Harriet Beecher Stowe",
    "Cecil Rhodes", "David Livingstone", "Henry Morton Stanley", "Karl Peters", "Paul Kruger",

    # ── Early 20th Century ──────────────────────────────────────────
    "Vladimir Lenin", "Leon Trotsky", "Joseph Stalin", "Rosa Luxemburg", "Karl Liebknecht",
    "Sun Yat-sen", "Yuan Shikai", "Chiang Kai-shek", "Mao Zedong", "Zhou Enlai",
    "Mahatma Gandhi", "Jawaharlal Nehru", "Subhas Chandra Bose", "B. R. Ambedkar", "Muhammad Ali Jinnah",
    "Winston Churchill", "Neville Chamberlain", "David Lloyd George", "Clement Attlee", "Ernest Bevin",
    "Franklin D. Roosevelt", "Woodrow Wilson", "Theodore Roosevelt", "Herbert Hoover", "Harry S. Truman",
    "Adolf Hitler", "Benito Mussolini", "Francisco Franco", "Hirohito", "Hideki Tojo",
    "Albert Einstein", "Marie Curie", "Max Planck", "Werner Heisenberg", "Niels Bohr",
    "Sigmund Freud", "Carl Jung", "Alfred Adler", "Wilhelm Reich", "Wilhelm Wundt",
    "Friedrich Nietzsche", "Martin Heidegger", "Edmund Husserl", "Bertrand Russell", "Ludwig Wittgenstein",
    "Pablo Picasso", "Salvador Dalí", "Marcel Duchamp", "Wassily Kandinsky", "Henri Matisse",
    "James Joyce", "Franz Kafka", "Marcel Proust", "Virginia Woolf", "T.S. Eliot",
    "John D. Rockefeller", "Andrew Carnegie", "J.P. Morgan", "Henry Ford", "Thomas Watson Sr.",

    # ── Mid–Late 20th Century ───────────────────────────────────────
    "Dwight D. Eisenhower", "John F. Kennedy", "Lyndon B. Johnson", "Richard Nixon", "Ronald Reagan",
    "Nikita Khrushchev", "Leonid Brezhnev", "Mikhail Gorbachev", "Boris Yeltsin", "Andrei Sakharov",
    "Mao Zedong", "Deng Xiaoping", "Zhou Enlai", "Lin Biao", "Peng Dehuai",
    "Nelson Mandela", "Kwame Nkrumah", "Patrice Lumumba", "Haile Selassie", "Jomo Kenyatta",
    "Ho Chi Minh", "Vo Nguyen Giap", "Pol Pot", "Sukarno", "Suharto",
    "Gamal Abdel Nasser", "Anwar Sadat", "Yasser Arafat", "David Ben-Gurion", "Golda Meir",
    "Fidel Castro", "Che Guevara", "Salvador Allende", "Augusto Pinochet", "Juan Perón",
    "Martin Luther King Jr.", "Malcolm X", "Thurgood Marshall", "Medgar Evers", "Rosa Parks",
    "Alan Turing", "John von Neumann", "Claude Shannon", "Norbert Wiener", "Richard Feynman",
    "Margaret Thatcher", "Charles de Gaulle", "Konrad Adenauer", "Willy Brandt", "Helmut Schmidt",
    "Mother Teresa", "Billy Graham", "Pope John XXIII", "Pope John Paul II", "Desmond Tutu",
    "Steve Jobs", "Bill Gates", "Jeff Bezos", "Elon Musk", "Mark Zuckerberg",
    "Muhammad Ali", "Pelé", "Ayrton Senna", "Roger Federer", "Michael Jordan",
    "Stephen Hawking", "Tim Berners-Lee", "James Watson", "Francis Crick", "Jonas Salk",
    "George Orwell", "Albert Camus", "Simone de Beauvoir", "Hannah Arendt", "Michel Foucault",
]

# Remove duplicates while preserving order
seen = set()
FIGURES_UNIQUE = []
for f in FIGURES:
    if f.lower() not in seen:
        seen.add(f.lower())
        FIGURES_UNIQUE.append(f)

def get_existing_names():
    try:
        res = requests.get(f"{API}/figures/", timeout=10)
        return {f["name"].lower() for f in res.json()}
    except:
        return set()

def analyze_figure(name):
    try:
        res = requests.post(
            f"{API}/analyze/",
            json={"name": name},
            timeout=60
        )
        if res.status_code == 200:
            return True, None
        else:
            return False, res.json().get("detail", "unknown error")
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, str(e)

def main():
    print(f"Total figures in list: {len(FIGURES_UNIQUE)}")
    print(f"Checking existing figures in database...")
    existing = get_existing_names()
    print(f"Already in database: {len(existing)} figures\n")

    to_import = [f for f in FIGURES_UNIQUE if f.lower() not in existing]
    print(f"To import: {len(to_import)} figures")
    print(f"Estimated time: {len(to_import) * 7 // 60}–{len(to_import) * 12 // 60} minutes\n")

    if not to_import:
        print("All figures already imported!")
        return

    success = 0
    failed = []

    for i, name in enumerate(to_import, 1):
        sys.stdout.write(f"[{i}/{len(to_import)}] {name}... ")
        sys.stdout.flush()

        ok, err = analyze_figure(name)
        if ok:
            success += 1
            print("✓")
        else:
            failed.append((name, err))
            print(f"✗  ({err})")

        if i < len(to_import):
            time.sleep(4)

    print(f"\n{'='*50}")
    print(f"Done: {success} imported, {len(failed)} failed")
    if failed:
        print("\nFailed figures (can re-run script to retry):")
        for name, err in failed:
            print(f"  - {name}: {err}")

if __name__ == "__main__":
    main()
