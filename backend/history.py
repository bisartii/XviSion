import sqlite3
from datetime import datetime

conn = sqlite3.connect("events.db")
cursor = conn.cursor()


def show_events(query, params=()):

    cursor.execute(query, params)
    events = cursor.fetchall()

    if not events:
        print("\nNo events found.")
        return

    print("\n" + "=" * 75)
    print(
        f"{'ID':<5}"
        f"{'Person':<15}"
        f"{'Time':<22}"
        f"{'Score':<10}"
        f"{'Track ID':<10}"
    )
    print("-" * 75)

    for event in events:

        event_id, person, time, score, track_id = event

        print(
            f"{event_id:<5}"
            f"{person:<15}"
            f"{time:<22}"
            f"{score:<10.2f}"
            f"{track_id:<10}"
        )

    print("=" * 75)


while True:

    print("\n========== FACE HISTORY ==========")
    print("1. Show all events")
    print("2. Show today's events")
    print("3. Search person")
    print("4. Show unknown people")
    print("5. Exit")

    choice = input("\nChoose: ")

    # -----------------------------
    # All events
    # -----------------------------

    if choice == "1":

        show_events("""
            SELECT id, person, time, confidence, track_id
            FROM events
            ORDER BY id DESC
        """)

    # -----------------------------
    # Today's events
    # -----------------------------

    elif choice == "2":

        today = datetime.now().strftime("%Y-%m-%d")

        show_events("""
            SELECT id, person, time, confidence, track_id
            FROM events
            WHERE time LIKE ?
            ORDER BY id DESC
        """, (today + "%",))

    # -----------------------------
    # Search person
    # -----------------------------

    elif choice == "3":

        name = input("Enter person's name: ").strip()

        show_events("""
            SELECT id, person, time, confidence, track_id
            FROM events
            WHERE LOWER(person) = LOWER(?)
            ORDER BY id DESC
        """, (name,))

    # -----------------------------
    # Unknown people
    # -----------------------------

    elif choice == "4":

        show_events("""
            SELECT id, person, time, confidence, track_id
            FROM events
            WHERE person = 'Unknown'
            ORDER BY id DESC
        """)

    # -----------------------------
    # Exit
    # -----------------------------

    elif choice == "5":

        print("\nExiting...")
        break

    else:

        print("\nInvalid choice!")

conn.close()