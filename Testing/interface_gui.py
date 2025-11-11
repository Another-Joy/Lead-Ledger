# interface_gui.py
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import playtest_db
from playtest_db import ensure_tag

DB_FILE = "playtest_history.sqlite3"
# Action types available in the dropdown and their categories
BIG_ACTIONS = ["Advance", "Embark", "Disembark", "Salvo", "Capture", "OverWatch", "OverWatch Shot"]
SMALL_ACTIONS = ["Skip", "Deploy", "Move", "Consolidate", "Control", "Shot", "Check Shot"]
SPECIAL_ACTIONS = ["Deploy", "OverWatch Shot", "Check Shot"]  # These actions don't increase turn counter
ACTION_TYPES = BIG_ACTIONS + SMALL_ACTIONS

def calculate_turn_number(actions):
    """Calculate turn number for each action based on player changes and action type"""
    turn = 1
    last_player = None
    turns = {}
    
    for action in actions:
        action_id = action['id']
        player = action['player']
        action_type = action['type']
        
        if last_player and player != last_player and action_type not in SPECIAL_ACTIONS:
            turn += 1
        
        turns[action_id] = turn
        
        if action_type not in SPECIAL_ACTIONS:
            last_player = player
            
    return turns

def init_if_needed():
    """Initialize database if it doesn't exist"""
    import playtest_db
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Sessions'")
    if not cur.fetchone():
        playtest_db.init_db(conn)
    conn.close()

def load_sessions():
    """Load and display all sessions in the sessions treeview"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.date, s.version, s.notes,
               GROUP_CONCAT(p.name, ' vs ') as players
        FROM Sessions s
        LEFT JOIN SessionPlayers sp ON sp.session_id = s.id
        LEFT JOIN Players p ON p.id = sp.player_id
        GROUP BY s.id
        ORDER BY s.date DESC
    """)
    sessions = cur.fetchall()
    conn.close()
    
    # Clear existing items
    for item in sessions_tree.get_children():
        sessions_tree.delete(item)
    
    # Insert sessions, ensuring values are in the correct order
    for session in sessions:
        # session tuple has values in order: id, date, version, notes, players
        sessions_tree.insert("", "end", values=session)

def get_session_players(session_id):
    """Get players for a session for the player dropdown"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name 
        FROM Players p 
        JOIN SessionPlayers sp ON sp.player_id = p.id 
        WHERE sp.session_id = ?
    """, (session_id,))
    players = cur.fetchall()
    conn.close()
    return players  # Updated to match playtest_db.py



def on_session_select(event):
    """Handle session selection to show its actions"""
    selected = sessions_tree.selection()
    if not selected:
        return
    
    # Get session id from selected item
    session_id = sessions_tree.item(selected[0])['values'][0]
    
    # Use playtest_db to get full action details
    conn = connect()
    import playtest_db
    actions = playtest_db.actions_for_session(conn, session_id)
    
    # Update player dropdown with session players
    players = playtest_db.get_session_players(conn, session_id)
    player_names = [p[1] for p in players]
    player_dropdown['values'] = player_names
    
    conn.close()
    
    # Clear existing items
    for item in actions_tree.get_children():
        actions_tree.delete(item)
    
    # Calculate turn numbers
    turn_numbers = calculate_turn_number(actions)
    
    # Insert actions with full details including participants and tags
    for action in actions:
        # Format participants
        participants_str = action['primary_participant'] or ''
        if action['secondary_participants']:
            if participants_str:
                participants_str += " → "
            participants_str += ", ".join(action['secondary_participants'])
        
        # Format tags
        tags_str = ", ".join(action['tags'])
        
        values = [
            turn_numbers[action['id']],  # Turn number instead of ID
            action['player'],
            action['type'],
            participants_str,
            tags_str,
            action['notes']
        ]
        # Store the action ID as a tag for reference when needed
        actions_tree.insert("", "end", values=values, tags=[action['id']])
        
    # Update selected session label and entry
    selected_session.set(f"Selected Session: {session_id}")
    entry_session.delete(0, tk.END)
    entry_session.insert(0, str(session_id))


def connect():
    return sqlite3.connect(DB_FILE)



def handle_enter(event):
    widget = event.widget
    
    # Define the widget sequences for both forms
    sequence1 = [action_type_dropdown, primary_participant, secondary_participants, entry_tags, entry_notes]
    sequence2 = [action_type_dropdown2, primary_participant2, secondary_participants2, entry_tags2, entry_notes2]
    
    # Special handling for the last widgets in each form
    if widget == entry_notes:
        action_type_dropdown2.focus()
        return "break"
    elif widget == entry_notes2:
        # After adding actions, will jump back to first form's action type
        combined_button.invoke()
        action_type_dropdown.focus()
        return "break"
    
    try:
        # Check if widget is in first sequence
        if widget in sequence1:
            next_idx = sequence1.index(widget) + 1
            if next_idx < len(sequence1):
                sequence1[next_idx].focus()
            else:
                # If it's the last widget in sequence 1, move to first widget in sequence 2
                primary_participant2.focus()
        # Check if widget is in second sequence
        elif widget in sequence2:
            next_idx = sequence2.index(widget) + 1
            if next_idx < len(sequence2):
                sequence2[next_idx].focus()
            else:
                # If it's the last widget in sequence 2, trigger combined button
                combined_button.invoke()
                # Move focus back to first field
                primary_participant.focus()
    except ValueError:
        pass  # Widget not in sequence
    
    return "break"  # Prevent default Enter behavior

def add_both_actions():
    """Add both actions in sequence"""
    # Add first action
    if primary_participant.get().strip() or secondary_participants.get().strip() or entry_tags.get().strip() or entry_notes.get().strip():
        add_action(form_num=1)
    
    # Add second action if it has any content
    if primary_participant2.get().strip() or secondary_participants2.get().strip() or entry_tags2.get().strip() or entry_notes2.get().strip():
        add_action(form_num=2)
    
    # Focus on first form's action type
    action_type_dropdown.focus()

def add_action(event=None, form_num=1):
    if not entry_session.get():
        messagebox.showerror("Error", "Please select a session first")
        return
        
    conn = connect()
    try:
        # Get the shared player and form-specific widgets
        if form_num == 1:
            primary = primary_participant.get().strip() or None
            secondary = [p.strip() for p in secondary_participants.get().split(',') if p.strip()] if secondary_participants.get() else None
            tags = [t.strip() for t in entry_tags.get().split(',')] if entry_tags.get() else None
        else:
            primary = primary_participant2.get().strip() or None
            secondary = [p.strip() for p in secondary_participants2.get().split(',') if p.strip()] if secondary_participants2.get() else None
            tags = [t.strip() for t in entry_tags2.get().split(',')] if entry_tags2.get() else None
        current_player = player_var.get()
        if not current_player:
            messagebox.showerror("Error", "Please select a player first")
            return
            
        # Get the correct variables based on form number
        if form_num == 1:
            current_action = action_type_var.get()
            entry_notes_widget = entry_notes
            primary_widget = primary_participant
            secondary_widget = secondary_participants
            entry_tags_widget = entry_tags
        else:
            current_action = action_type_var2.get()
            entry_notes_widget = entry_notes2
            primary_widget = primary_participant2
            secondary_widget = secondary_participants2
            entry_tags_widget = entry_tags2
            
        # Validate action type
        if not current_action:
            messagebox.showerror("Error", "Please select an action type")
            return
        if current_action not in ACTION_TYPES:
            messagebox.showerror("Error", f"Invalid action type: {current_action}")
            return

        if current_action in ["Deploy", "Advance", "Capture", "Move", "Control"]:
            secondary = [sec.upper() for sec in secondary] if secondary else None 
        
        # Use the playtest_db function to add the action with all details
        playtest_db.add_action(
            conn,
            int(entry_session.get()),
            current_player,
            current_action,
            entry_notes_widget.get(),
            primary_participant=primary,
            secondary_participants=secondary,
            tags=tags
        )
        
        # Switch player for small actions
        if current_action in SMALL_ACTIONS:
            # Get list of players and find current index
            players = list(player_dropdown['values'])
            if len(players) > 1:  # Only switch if there are at least 2 players
                current_idx = players.index(current_player)
                next_idx = (current_idx + 1) % len(players)
                player_var.set(players[next_idx])
        
        # Clear fields
        entry_notes_widget.delete(0, tk.END)
        primary_widget.delete(0, tk.END)
        secondary_widget.delete(0, tk.END)
        entry_tags_widget.delete(0, tk.END)
        
        # Reset action type dropdown
        if form_num == 1:
            action_type_var.set('')
        else:
            action_type_var2.set('')
        
        # Refresh the actions list if this action belongs to the currently selected session
        selected = sessions_tree.selection()
        if selected and str(sessions_tree.item(selected[0])['values'][0]) == entry_session.get():
            on_session_select(None)
        
        messagebox.showinfo("Added", "Action added")
        # Set focus back to primary participant field
        primary_participant.focus()
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()

# GUI setup
root = tk.Tk()
root.title("Playtest History")

# Initialize database if needed
init_if_needed()

# Add a refresh button at the top
refresh_btn = tk.Button(root, text="Refresh Lists", command=lambda: load_sessions())
refresh_btn.pack(fill="x", padx=5, pady=5)

# Create PanedWindow for resizable split
lists_pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
lists_pane.pack(fill="both", expand=True, padx=5, pady=5)

# Top half for lists
lists_frame = tk.Frame(lists_pane)
lists_pane.add(lists_frame, weight=1)

# Sessions list
sessions_frame = tk.LabelFrame(lists_frame, text="Sessions")
sessions_frame.pack(side="left", fill="both", expand=True, padx=5)

sessions_tree = ttk.Treeview(sessions_frame, columns=("id", "date", "version", "notes", "players"), show="headings")
sessions_tree.heading("id", text="ID")
sessions_tree.heading("date", text="Date")
sessions_tree.heading("version", text="Version")
sessions_tree.heading("notes", text="Notes")
sessions_tree.heading("players", text="Players")

# Configure column widths
sessions_tree.column("id", width=50, minwidth=50)
sessions_tree.column("date", width=100, minwidth=100)
sessions_tree.column("version", width=70, minwidth=70)
sessions_tree.column("notes", width=150, minwidth=100)
sessions_tree.column("players", width=150, minwidth=100)

sessions_tree.pack(fill="both", expand=True)
sessions_tree.bind("<Double-1>", on_session_select)

# Add Delete Session button
def delete_session():
    selected = sessions_tree.selection()
    if not selected:
        messagebox.showerror("Error", "Please select a session to delete")
        return
    
    if not messagebox.askyesno("Confirm Delete", "Delete this session and all its actions?"):
        return
        
    session_id = sessions_tree.item(selected[0])['values'][0]
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM Sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    load_sessions()
    
    # Clear session-related fields
    entry_session.delete(0, tk.END)
    selected_session.set("Selected Session: None")
    # Clear actions tree
    for item in actions_tree.get_children():
        actions_tree.delete(item)

# Buttons frame for session operations
session_buttons_frame = tk.Frame(sessions_frame)
session_buttons_frame.pack(pady=5)

delete_session_btn = tk.Button(session_buttons_frame, text="Delete Session", command=delete_session)
delete_session_btn.pack(side=tk.LEFT, padx=2)

def show_add_session_dialog():
    dialog = SessionDialog(root)
    root.wait_window(dialog.dialog)
    if dialog.result:
        conn = connect()
        try:
            playtest_db.add_session(conn, 
                               dialog.result['version'],
                               dialog.result['player1'],
                               dialog.result['player2'],
                               notes=dialog.result['notes'])
            messagebox.showinfo("Success", "Session added successfully")
            load_sessions()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

add_session_btn = tk.Button(session_buttons_frame, text="Add Session", command=show_add_session_dialog)
add_session_btn.pack(side=tk.LEFT, padx=2)

# Edit Action Dialog
class EditActionDialog:
    def __init__(self, parent, action_data):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Action")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.result = None
        self.action_data = action_data
        
        # Create widgets
        tk.Label(self.dialog, text="Type").grid(row=0, column=0)
        self.type_var = tk.StringVar(value=action_data['type'])
        self.type_combo = ttk.Combobox(self.dialog, textvariable=self.type_var, values=ACTION_TYPES, state="readonly")
        self.type_combo.grid(row=0, column=1)
        
        tk.Label(self.dialog, text="Primary Participant").grid(row=1, column=0)
        self.primary = tk.Entry(self.dialog)
        self.primary.insert(0, action_data['primary_participant'] or '')
        self.primary.grid(row=1, column=1)
        
        tk.Label(self.dialog, text="Secondary Participants").grid(row=2, column=0)
        self.secondary = tk.Entry(self.dialog)
        if action_data['secondary_participants']:
            self.secondary.insert(0, ', '.join(action_data['secondary_participants']))
        self.secondary.grid(row=2, column=1)
        
        tk.Label(self.dialog, text="Tags").grid(row=3, column=0)
        self.tags = tk.Entry(self.dialog)
        if action_data['tags']:
            self.tags.insert(0, ', '.join(action_data['tags']))
        self.tags.grid(row=3, column=1)
        
        tk.Label(self.dialog, text="Notes").grid(row=4, column=0)
        self.notes = tk.Entry(self.dialog)
        self.notes.insert(0, action_data['notes'] or '')
        self.notes.grid(row=4, column=1)
        
        btn_frame = tk.Frame(self.dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save
        self.dialog.bind("<Return>", lambda e: self.save())
        self.dialog.bind("<Escape>", lambda e: self.cancel())
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def save(self):
        self.result = {
            'type': self.type_var.get(),
            'primary_participant': self.primary.get().strip() or None,
            'secondary_participants': [p.strip() for p in self.secondary.get().split(',')] if self.secondary.get().strip() else None,
            'tags': [t.strip() for t in self.tags.get().split(',')] if self.tags.get().strip() else None,
            'notes': self.notes.get().strip() or ""
        }
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()

# Actions list
actions_frame = tk.LabelFrame(lists_frame, text="Actions")
actions_frame.pack(side="right", fill="both", expand=True, padx=5)

selected_session = tk.StringVar(value="Selected Session: None")
tk.Label(actions_frame, textvariable=selected_session).pack()

actions_tree = ttk.Treeview(actions_frame, columns=("turn", "player", "type", "participants", "tags", "notes"), show="headings")
actions_tree.heading("turn", text="Turn")
actions_tree.heading("player", text="Player")
actions_tree.heading("type", text="Type")
actions_tree.heading("participants", text="Participants")
actions_tree.heading("tags", text="Tags")
actions_tree.heading("notes", text="Notes")

# Configure column widths
actions_tree.column("turn", width=50, minwidth=50)
actions_tree.column("player", width=80, minwidth=80)
actions_tree.column("type", width=80, minwidth=80)
actions_tree.column("participants", width=100, minwidth=100)
actions_tree.column("tags", width=80, minwidth=80)
actions_tree.column("notes", width=250, minwidth=100)

actions_tree.pack(fill="both", expand=True)

# Add double-click handler for action editing
def on_action_double_click(event):
    selected = actions_tree.selection()
    if not selected:
        return
        
    selected_item = actions_tree.item(selected[0])
    action = selected_item['values']
    action_id = selected_item['tags'][0]  # Get ID from tags

    action_data = {
        'id': action_id,
        'player': action[1],
        'type': action[2],
        'notes': action[5],
        'primary_participant': None,
        'secondary_participants': [],
        'tags': []
    }
    
    # Parse participants from the participants string
    if action[3]:  # participants column
        parts = action[3].split(' → ')
        if parts[0]:  # primary participant
            action_data['primary_participant'] = parts[0]
        if len(parts) > 1:  # secondary participants
            action_data['secondary_participants'] = [p.strip() for p in parts[1].split(',')]
    
    # Parse tags
    if action[4]:  # tags column
        action_data['tags'] = [t.strip() for t in action[4].split(',')]
    
    dialog = EditActionDialog(root, action_data)
    root.wait_window(dialog.dialog)
    
    if dialog.result:
        conn = connect()
        cur = conn.cursor()
        
        # Update the action
        cur.execute("""
            UPDATE Actions 
            SET type = ?, notes = ?
            WHERE id = ?
        """, (dialog.result['type'], dialog.result['notes'], action_data['id']))
        
        # Delete old participants
        cur.execute("DELETE FROM ActionParticipants WHERE action_id = ?", (action_data['id'],))
        
        # Add new primary participant
        if dialog.result['primary_participant']:
            cur.execute(
                "INSERT INTO ActionParticipants (action_id, is_primary, name_text) VALUES (?, ?, ?)",
                (action_data['id'], True, dialog.result['primary_participant'])
            )
        
        # Add new secondary participants
        if dialog.result['secondary_participants']:
            cur.executemany(
                "INSERT INTO ActionParticipants (action_id, is_primary, name_text) VALUES (?, ?, ?)",
                [(action_data['id'], False, name) for name in dialog.result['secondary_participants']]
            )
            
        # Delete old tags
        cur.execute("DELETE FROM ActionTags WHERE action_id = ?", (action_data['id'],))
        
        # Add new tags
        if dialog.result['tags']:
            for tag in dialog.result['tags']:
                tag_id = ensure_tag(conn, tag)
                cur.execute("INSERT INTO ActionTags (action_id, tag_id) VALUES (?, ?)", 
                          (action_data['id'], tag_id))
        
        conn.commit()
        conn.close()
        
        # Refresh the actions list
        on_session_select(None)

def delete_action():
    selected = actions_tree.selection()
    if not selected:
        messagebox.showerror("Error", "Please select an action to delete")
        return
    
    if not messagebox.askyesno("Confirm Delete", "Delete this action?"):
        return
        
    action_id = actions_tree.item(selected[0])['tags'][0]  # Get ID from tags
    conn = connect()
    cur = conn.cursor()
    
    # Delete related records first (foreign key references)
    cur.execute("DELETE FROM ActionTags WHERE action_id = ?", (action_id,))
    cur.execute("DELETE FROM ActionParticipants WHERE action_id = ?", (action_id,))
    
    # Then delete the action itself
    cur.execute("DELETE FROM Actions WHERE id = ?", (action_id,))
    conn.commit()
    conn.close()
    
    # Refresh actions list
    selected = sessions_tree.selection()
    if selected:
        on_session_select(None)

delete_action_btn = tk.Button(actions_frame, text="Delete Action", command=delete_action)
delete_action_btn.pack(pady=5)

# Bind double-click for editing
actions_tree.bind("<Double-1>", on_action_double_click)

# Session Dialog class
class SessionDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Session")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        window_width = 300
        window_height = 200
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Create and pack the form elements
        tk.Label(self.dialog, text="Version").grid(row=0, column=0, padx=5, pady=5)
        self.version = tk.Entry(self.dialog)
        self.version.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.dialog, text="Player 1").grid(row=1, column=0, padx=5, pady=5)
        self.player1 = tk.Entry(self.dialog)
        self.player1.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.dialog, text="Player 2").grid(row=2, column=0, padx=5, pady=5)
        self.player2 = tk.Entry(self.dialog)
        self.player2.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self.dialog, text="Notes").grid(row=3, column=0, padx=5, pady=5)
        self.notes = tk.Entry(self.dialog)
        self.notes.grid(row=3, column=1, padx=5, pady=5)

        # Buttons frame
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        self.result = None
        
    def save(self):
        self.result = {
            'version': self.version.get(),
            'player1': self.player1.get(),
            'player2': self.player2.get(),
            'notes': self.notes.get()
        }
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

# Create bottom frame to hold add and search frames side by side
bottom_frame = tk.Frame(lists_pane)
lists_pane.add(bottom_frame, weight=1)  # Equal weight for 50/50 split

# Add Action frames container
actions_input_frame = tk.Frame(bottom_frame)
actions_input_frame.pack(side="left", fill="both", expand=True, padx=(0,5))

# First Action frame
frame2 = tk.LabelFrame(actions_input_frame, text="Action 1")
frame2.pack(side="left", fill="both", expand=True, padx=(0,5))

# Second Action frame
frame3 = tk.LabelFrame(actions_input_frame, text="Action 2")
frame3.pack(side="left", fill="both", expand=True, padx=(0,5))

# Session ID (hidden but needed)
entry_session = tk.Entry(frame2)
entry_session.grid_remove()  # Hide it, it's set automatically when selecting a session

# Search frame
search_frame = tk.LabelFrame(bottom_frame, text="Search Actions")
search_frame.pack(side="right", fill="y", expand=True, padx=(5,0))

def get_all_versions():
    """Get list of all versions in database"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT version FROM Sessions ORDER BY version")
    versions = [row[0] for row in cur.fetchall()]
    conn.close()
    return versions

def update_search_results(*args):
    """Update search results based on current search parameters"""
    conn = connect()
    cur = conn.cursor()
    
    # Base query parts
    params = []
    where_clauses = []
    
    # Add version filter if specified
    if version_var.get():
        where_clauses.append("s.version = ?")
        params.append(version_var.get())
    
    # Add action type filter if specified
    if action_type_search.get():
        where_clauses.append("a.type = ?")
        params.append(action_type_search.get())
    
    # Add primary participant filter if specified
    if primary_search.get():
        where_clauses.append("""EXISTS (
            SELECT 1 FROM ActionParticipants ap 
            WHERE ap.action_id = a.id 
            AND ap.is_primary = 1 
            AND ap.name_text LIKE ?
        )""")
        params.append(f"%{primary_search.get()}%")
    
    # Add secondary participant filter if specified
    if secondary_search.get():
        where_clauses.append("""EXISTS (
            SELECT 1 FROM ActionParticipants ap 
            WHERE ap.action_id = a.id 
            AND ap.is_primary = 0 
            AND ap.name_text LIKE ?
        )""")
        params.append(f"%{secondary_search.get()}%")
    
    # Add tags filter if specified
    if tags_search.get():
        where_clauses.append("""EXISTS (
            SELECT 1 FROM ActionTags at
            JOIN Tags t ON t.id = at.tag_id
            WHERE at.action_id = a.id
            AND t.name LIKE ?
        )""")
        params.append(f"%{tags_search.get()}%")
    
    # Base query
    query = """
    SELECT COUNT(DISTINCT a.id)
    FROM Actions a
    JOIN Sessions s ON s.id = a.session_id
    """
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    # Get total count
    cur.execute(query, params)
    total_count = cur.fetchone()[0]
    result_text = f"Total matching actions: {total_count}\n\n"
    
    # Handle grouping for checked items
    if version_check.get():
        cur.execute(f"""
            SELECT s.version, COUNT(DISTINCT a.id)
            FROM Actions a
            JOIN Sessions s ON s.id = a.session_id
            {' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
            GROUP BY s.version
            ORDER BY COUNT(DISTINCT a.id) DESC
        """, params)
        result_text += "By Version: "
        result_text += ", ".join(f"{row[0]}({row[1]})" for row in cur.fetchall()) + "\n"
    
    if type_check.get():
        cur.execute(f"""
            SELECT a.type, COUNT(DISTINCT a.id)
            FROM Actions a
            JOIN Sessions s ON s.id = a.session_id
            {' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
            GROUP BY a.type
            ORDER BY COUNT(DISTINCT a.id) DESC
        """, params)
        result_text += "By Type: "
        result_text += ", ".join(f"{row[0]}({row[1]})" for row in cur.fetchall()) + "\n"
    
    if primary_check.get():
        cur.execute(f"""
            SELECT ap.name_text, COUNT(DISTINCT a.id)
            FROM Actions a
            JOIN Sessions s ON s.id = a.session_id
            JOIN ActionParticipants ap ON ap.action_id = a.id
            WHERE ap.is_primary = 1
            {' AND ' + ' AND '.join(where_clauses) if where_clauses else ''}
            GROUP BY ap.name_text
            ORDER BY COUNT(DISTINCT a.id) DESC
        """, params)
        result_text += "By Primary: "
        result_text += ", ".join(f"{row[0]}({row[1]})" for row in cur.fetchall()) + "\n"
    
    if secondary_check.get():
        cur.execute(f"""
            SELECT ap.name_text, COUNT(DISTINCT a.id)
            FROM Actions a
            JOIN Sessions s ON s.id = a.session_id
            JOIN ActionParticipants ap ON ap.action_id = a.id
            WHERE ap.is_primary = 0
            {' AND ' + ' AND '.join(where_clauses) if where_clauses else ''}
            GROUP BY ap.name_text
            ORDER BY COUNT(DISTINCT a.id) DESC
        """, params)
        result_text += "By Secondary: "
        result_text += ", ".join(f"{row[0]}({row[1]})" for row in cur.fetchall()) + "\n"
    
    if tags_check.get():
        cur.execute(f"""
            SELECT t.name, COUNT(DISTINCT a.id)
            FROM Actions a
            JOIN Sessions s ON s.id = a.session_id
            JOIN ActionTags at ON at.action_id = a.id
            JOIN Tags t ON t.id = at.tag_id
            {' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
            GROUP BY t.name
            ORDER BY COUNT(DISTINCT a.id) DESC
        """, params)
        result_text += "By Tag: "
        result_text += ", ".join(f"{row[0]}({row[1]})" for row in cur.fetchall()) + "\n"
    
    # Update results text widget with word wrap
    results_text.delete(1.0, tk.END)
    results_text.insert(tk.END, result_text)
    
    conn.close()

# Version
tk.Label(search_frame, text="Version").grid(row=0, column=0, sticky="w")
version_var = tk.StringVar()
version_dropdown = ttk.Combobox(search_frame, textvariable=version_var, values=get_all_versions(), state="readonly")
version_dropdown.grid(row=0, column=1, sticky="ew")
version_check = tk.BooleanVar()
tk.Checkbutton(search_frame, variable=version_check, command=update_search_results).grid(row=0, column=2)

# Action Type
tk.Label(search_frame, text="Action Type").grid(row=1, column=0, sticky="w")
action_type_search = tk.Entry(search_frame)
action_type_search.grid(row=1, column=1, sticky="ew")
type_check = tk.BooleanVar()
tk.Checkbutton(search_frame, variable=type_check, command=update_search_results).grid(row=1, column=2)

# Primary
tk.Label(search_frame, text="Primary").grid(row=2, column=0, sticky="w")
primary_search = tk.Entry(search_frame)
primary_search.grid(row=2, column=1, sticky="ew")
primary_check = tk.BooleanVar()
tk.Checkbutton(search_frame, variable=primary_check, command=update_search_results).grid(row=2, column=2)

# Secondary
tk.Label(search_frame, text="Secondary").grid(row=3, column=0, sticky="w")
secondary_search = tk.Entry(search_frame)
secondary_search.grid(row=3, column=1, sticky="ew")
secondary_check = tk.BooleanVar()
tk.Checkbutton(search_frame, variable=secondary_check, command=update_search_results).grid(row=3, column=2)

# Tags
tk.Label(search_frame, text="Tags").grid(row=4, column=0, sticky="w")
tags_search = tk.Entry(search_frame)
tags_search.grid(row=4, column=1, sticky="ew")
tags_check = tk.BooleanVar()
tk.Checkbutton(search_frame, variable=tags_check, command=update_search_results).grid(row=4, column=2)

# Results text area
results_text = tk.Text(search_frame, height=6, wrap=tk.WORD)
results_text.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=5)

# Configure search frame grid
search_frame.grid_columnconfigure(1, weight=1)

# Bind search field changes to update results
for widget in [version_dropdown, action_type_search, primary_search, secondary_search, tags_search]:
    if isinstance(widget, tk.Entry):
        widget.bind("<KeyRelease>", update_search_results)
    else:
        widget.bind("<<ComboboxSelected>>", update_search_results)

# Shared player selection at the top
player_frame = tk.Frame(actions_input_frame)
player_frame.pack(fill="x", pady=(0, 5))
tk.Label(player_frame, text="Player").pack(side="left", padx=5)
player_var = tk.StringVar()
player_dropdown = ttk.Combobox(player_frame, textvariable=player_var, state="readonly")
player_dropdown.pack(side="left", expand=True, fill="x", padx=5)

# Create input fields for both forms
def create_action_form(frame, form_num, action_types):
    # Use shared player dropdown

    # Action type dropdown with search functionality
    tk.Label(frame, text="Action Type").grid(row=0, column=0)
    action_type_var = tk.StringVar()
    action_type_dropdown = ttk.Combobox(frame, textvariable=action_type_var, values=action_types)
    action_type_dropdown.grid(row=0, column=1)
    action_type_dropdown.set('')  # Start empty

    def update_action_dropdown(event):
        current_text = action_type_var.get().lower()
        if current_text:
            matching_actions = [action for action in ACTION_TYPES if action.lower().startswith(current_text)]
            if matching_actions:
                action_type_dropdown['values'] = matching_actions
            else:
                action_type_dropdown['values'] = ACTION_TYPES
        else:
            action_type_dropdown['values'] = ACTION_TYPES

    def handle_action_enter(event):
        current_text = action_type_var.get().lower()
        matching_actions = [action for action in ACTION_TYPES if action.lower().startswith(current_text)]
        if matching_actions:
            action_type_var.set(matching_actions[0])
        action_type_dropdown['values'] = ACTION_TYPES  # Reset to full list
        # Move focus to next field
        if frame == frame2:  # First form
            primary_participant.focus()
        else:  # Second form
            primary_participant2.focus()

    action_type_dropdown.bind('<KeyRelease>', update_action_dropdown)
    action_type_dropdown.bind('<Return>', handle_action_enter)

    # Participants frame
    participants_frame = ttk.LabelFrame(frame, text="Participants")
    participants_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

    # Primary participant
    tk.Label(participants_frame, text="Primary").grid(row=0, column=0)
    primary_participant = tk.Entry(participants_frame)
    primary_participant.grid(row=0, column=1)
    primary_participant.bind("<Return>", handle_enter)

    # Secondary participants
    tk.Label(participants_frame, text="Secondary (comma-separated)").grid(row=1, column=0)
    secondary_participants = tk.Entry(participants_frame)
    secondary_participants.grid(row=1, column=1)
    secondary_participants.bind("<Return>", handle_enter)

    # Tags
    tk.Label(frame, text="Tags (comma-separated)").grid(row=3, column=0)
    entry_tags = tk.Entry(frame)
    entry_tags.grid(row=3, column=1)
    entry_tags.bind("<Return>", handle_enter)

    # Notes
    tk.Label(frame, text="Notes").grid(row=4, column=0)
    entry_notes = tk.Entry(frame)
    entry_notes.grid(row=4, column=1)
    entry_notes.bind("<Return>", handle_enter)
    
    tk.Button(frame, text=f"Add Action {form_num}", command=lambda: add_action(form_num=form_num)).grid(row=5, columnspan=2, pady=5)
    
    return {
        'player_var': player_var,
        'player_dropdown': player_dropdown,
        'action_type_var': action_type_var,
        'action_type_dropdown': action_type_dropdown,
        'primary_participant': primary_participant,
        'secondary_participants': secondary_participants,
        'entry_tags': entry_tags,
        'entry_notes': entry_notes
    }

# Create both forms with different action types
form1_widgets = create_action_form(frame2, 1, BIG_ACTIONS)
form2_widgets = create_action_form(frame3, 2, SMALL_ACTIONS)

# Add combined actions button
combined_button = tk.Button(actions_input_frame, text="Add Both Actions", command=add_both_actions)
combined_button.pack(side="bottom", pady=10, fill="x")

# Store widgets globally for handle_enter function
primary_participant = form1_widgets['primary_participant']
secondary_participants = form1_widgets['secondary_participants']
entry_tags = form1_widgets['entry_tags']
entry_notes = form1_widgets['entry_notes']
player_var = form1_widgets['player_var']
player_dropdown = form1_widgets['player_dropdown']
action_type_var = form1_widgets['action_type_var']
action_type_dropdown = form1_widgets['action_type_dropdown']

primary_participant2 = form2_widgets['primary_participant']
secondary_participants2 = form2_widgets['secondary_participants']
entry_tags2 = form2_widgets['entry_tags']
entry_notes2 = form2_widgets['entry_notes']
player_var2 = form2_widgets['player_var']
player_dropdown2 = form2_widgets['player_dropdown']
action_type_var2 = form2_widgets['action_type_var']
action_type_dropdown2 = form2_widgets['action_type_dropdown']

# Initial load
load_sessions()

root.mainloop()
