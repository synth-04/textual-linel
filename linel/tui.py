from linel.database import Database
from textual.app import App, on, ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, DataTable, Static, Input, Select, TextArea
import pathlib, os, random, csv

class DatabaseSelectionScreen(Screen):

    def __init__(self):
        super().__init__()

    def compose(self):

        database_dir = pathlib.Path(__file__).parent / "database"
        db_files = [f for f in os.listdir(database_dir) if f.endswith(".db")]

        if not db_files:
            yield Label("No databases found in the 'database' folder.")
            yield Button("New", id="new")
            yield Button("Cancel", id="cancel")
        else:
            yield Label("Select a database to load:")
            self.selection = Select.from_values(db_files)
            yield self.selection

            yield Button("New", id="new")
            yield Button("Load", id="load")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#new")
    def action_new(self):
        self.app.push_screen(NewDatabaseScreen())        

    @on(Button.Pressed, "#load")
    def action_load(self):
        selected_db = self.selection.value
    
        if selected_db != Select.BLANK:
            db_path = pathlib.Path(__file__).parent / "database" / selected_db
            self.app.set_database(db_path)
            self.app.push_screen(Home())
        else:
            print("No database selected")

    @on(Button.Pressed, "#cancel")
    def action_request_quit(self):
        def check_answer(accepted):
                if accepted:
                    self.app.exit()
        self.app.push_screen(QuestionDialog("Do you want to quit?"), check_answer)

class NewDatabaseScreen(Screen):

    def __init__(self):
        super().__init__()

    def compose(self):
            yield Label("Insert the name of the new database:")
            new_db = Input(classes="input", id="name")
            yield new_db

            
            yield Button("Create", id="create")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#create")
    def action_load(self):
        name_db = self.query_one("#name", Input).value + ".db"
    
        if name_db:
            db_path = pathlib.Path(__file__).parent / "database" / name_db
            self.app.set_database(db_path)
            self.app.push_screen(Home())
        else:
            print("No name")

    @on(Button.Pressed, "#cancel")       
    def action_cancel(self):
        self.app.push_screen(DatabaseSelectionScreen())

class Home(Screen):

    BINDINGS = [("a", "add", "Add word"),
                ("u", "modify", "Update word"),
                ("s", "search", "Search"),
                ("c", "upload_csv", "Upload csv"),
                ("d","delete", "Delete word")]

    def __init__(self):
        super().__init__()

    def compose(self):
        yield Header()
        self.linel_list = DataTable(classes="Words-list")
        self.linel_list.focus()
        self.linel_list.add_columns("ID","Word", "Type", "English", "Class/Declinations", "Root", "Notes")
        self.linel_list.cursor_type = "row"
        self.linel_list.zebra_stripes = True
        add_button = Button("Add", variant="success", id="add")
        modify_button = Button("Update", variant="success", id="modify")
        search_button = Button("Search", variant="success", id="search")
        upload_csv_button = Button("Upload CSV", variant = "success", id = "upload_csv")
        delete_button = Button("Delete", variant="warning", id="delete")
        add_button.focus()
        buttons_panel = Vertical(
            add_button,
            modify_button,
            search_button,
            upload_csv_button,
            delete_button,
            Static(classes="separator"),
            classes="buttons-panel",
        )
        yield Horizontal(self.linel_list, buttons_panel)
        yield Footer()

    def on_mount(self):
        self.db = self.app.db
        self._load_words()

    def _load_words(self):
        words_list = self.query_one(DataTable)
        words_list.clear()
        words = self.db.get_all_words()
    
        for word_data in words:
            word_id = word_data[0]
            if word_id:
                words_list.add_row(word_id, *word_data[1:], key=str(word_id))
            else:
                print(f"Invalid word ID: {word_id} for word: {word_data}")

    @on(Button.Pressed, "#add")
    def action_add(self):
        def check_word(word_data):
            if word_data:
                self.db.add_word(word_data)
                self._load_words()

        self.app.push_screen(AddDialog(), check_word)

    @on(Button.Pressed, "#modify")
    def action_modify(self):
        words_list = self.query_one(DataTable)

        if words_list.cursor_coordinate.row == 0:
            print("No row selected")
            return
        
        row_key, _ = words_list.coordinate_to_cell_key(words_list.cursor_coordinate)
            
        word_data = words_list.get_row(row_key)
        
        if not word_data:
            print(f"No data found for the selected row {row_key}")
            return

        word_id = row_key.value
        word_record = self.db.get_word_by_id(int(word_id))

        def handle_update(updated_word):
            if updated_word:
                self.db.update_word(word_id, updated_word)
                self._load_words()
        
        self.app.push_screen(UpdateDialog(word_record), handle_update)

    @on(Button.Pressed, "#search")
    def action_search(self):
        self.app.push_screen(QueryScreen(self.db))

    @on(Button.Pressed, "#upload_csv")
    def action_upload_csv(self):
        self.app.push_screen(CSVSelectionScreen(self.db))

    @on(Button.Pressed, "#delete")
    def action_delete(self):
        words_list = self.query_one(DataTable)

        if words_list.cursor_coordinate.row == 0:
            print("No row selected")
            return
        
        row_key, _ = words_list.coordinate_to_cell_key(words_list.cursor_coordinate)

        def check_answer(accepted):
            if accepted:
                self.db.delete_word(id=row_key.value)
                words_list.remove_row(row_key)

        word = words_list.get_row(row_key)[0]
        self.app.push_screen(
            QuestionDialog(f"Do you want to delete {word}?"),
                check_answer,
        )

class About(Screen):
    def compose(self):
        yield Header()
        yield Static("About This App\n\nA conlang tool to manage words in your constructed language.", id="about_text")
        yield Button("Back to Home", id="back")
        yield Footer()

class LinelApp(App):
    CSS_PATH = "linel.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("h", "switch_home", "Home"),
        ("b", "switch_about", "About"),
        ("w","switch_generator", "Word Generator")
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = None

    def set_database(self, db_path):
        self.db = Database(db_path)

    def on_mount(self):
        self.title = "LINEL"
        self.sub_title = "A Conlang Tool"

        self.push_screen(DatabaseSelectionScreen())

    def switch_to_home(self):
        self.push_screen(Home(db_path=self.db_path))

    def switch_to_about(self):
        self.push_screen(About())

    def switch_to_gen(self):
        self.push_screen(WordGeneratorScreen())

    @on(Button.Pressed, "#back")
    def return_home(self):
        self.switch_to_home()

    def action_toggle_dark(self):
        self.dark = not self.dark

    def action_request_quit(self):
        def check_answer(accepted):
            if accepted:
                self.exit()
        self.push_screen(QuestionDialog("Do you want to quit?"), check_answer)

    def action_switch_home(self):
        self.switch_to_home()

    def action_switch_about(self):
        self.switch_to_about()
    
    def action_switch_generator(self):
        self.switch_to_gen()

class QuestionDialog(Screen):
    def __init__(self, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    def compose(self):
        yes_button = Button("Yes", variant = "error", id="yes")
        no_button = Button("No", variant="primary", id="no")
        yes_button.focus()

        yield Grid(
            Label(self.message, id="question"),
            yes_button,
            no_button,
            id="question-dialog",
        )

    def on_button_pressed(self, event):
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

class AddDialog(Screen):

    def __init__(self):
        super().__init__()
    
    def compose(self):
        yield Grid(
            Label("Add Word", id="title"),
            Label("Word:", classes="label"),
            Input(
                placeholder="Word",
                classes="input",
                id="word",
            ),
            Label("Type:", classes="label"),
            Input(
                placeholder="Type",
                classes="input",
                id="type",
            ),
            Label("English:", classes="label"),
            Input(
                placeholder="English",
                classes="input",
                id="english",
            ),
            Label("Class/Declination:", classes="label"),
            Input(
                placeholder="Class/Declination",
                classes="input",
                id="class_decl",
            ),
            Label("Root:", classes="label"),
            Input(
                placeholder="Root",
                classes="input",
                id="root",
            ),
            Label("Notes:", classes="label"),
            Input(
                placeholder="Notes",
                classes="input",
                id="notes",
            ),
            Static(),
            Button("Save", variant="success", id="save"),
            Button("Cancel", variant="warning", id="back"),
            id="input-dialog",
        )   

    @on(Button.Pressed, '#save')
    def save(self):
        word = self.query_one("#word", Input).value
        type = self.query_one("#type", Input).value
        english = self.query_one("#english", Input).value
        class_decl = self.query_one("#class_decl", Input).value
        root = self.query_one("#root", Input).value
        notes = self.query_one("#notes", Input).value
        
        added_word = (word, type, english, class_decl, root, notes)
        self.dismiss(added_word)

class UpdateDialog(Screen):

    def __init__(self, word_record):
        super().__init__()
        self.word_record = word_record

    def compose(self):
        yield Grid(
            Label("Update Word", id="title"),
            Label("Word:", classes="label"),
            Input(
                value=self.word_record[1],
                placeholder="Word",
                classes="input",
                id="input-word",
            ),
            Label("Type:", classes="label"),
            Input(
                value=self.word_record[2],
                placeholder="Type",
                classes="input",
                id="input-type",
            ),
            Label("English:", classes="label"),
            Input(
                value=self.word_record[3],
                placeholder="English",
                classes="input",
                id="input-english",
            ),
            Label("Class/Declination:", classes="label"),
            Input(
                value=self.word_record[4],
                placeholder="Class/Declination",
                classes="input",
                id="input-class_decl",
            ),
            Label("Root:", classes="label"),
            Input(
                value=self.word_record[5],
                placeholder="Root",
                classes="input",
                id="input-root",
            ),
            Label("Notes:", classes="label"),
            Input(
                value=self.word_record[6],
                placeholder="Notes",
                classes="input",
                id="input-notes",
            ),
            Static(),
            Button("Save", variant="success", id="save"),
            Button("Cancel", variant="warning", id="back"),
            id="input-dialog",
        )

    @on(Button.Pressed, "#save")
    def save_changes(self):
        new_word = self.query_one("#input-word", Input).value
        new_type = self.query_one("#input-type", Input).value
        new_english = self.query_one("#input-english", Input).value
        new_class_decl = self.query_one("#input-class_decl", Input).value
        new_root = self.query_one("#input-root", Input).value
        new_notes = self.query_one("#input-notes", Input).value

        updated_word = (new_word, new_type, new_english, new_class_decl, new_root, new_notes)
        
        self.dismiss(updated_word)

class QueryScreen(Screen):

    def __init__(self, db):
        super().__init__()
        self.db = db

    def compose(self):
        yield Header()
        yield Grid(
            Label("Search", id="title"),
            Label("Word:", classes="label"),
            Input(
                value=None,
                placeholder="Word",
                classes="input",
                id="input-word",
            ),
            Label("Type:", classes="label"),
            Input(
                value=None,
                placeholder="Type",
                classes="input",
                id="input-type",
            ),
            Label("English:", classes="label"),
            Input(
                value=None,
                placeholder="English",
                classes="input",
                id="input-english",
            ),
            Label("Class/Declination:", classes="label"),
            Input(
                value=None,
                placeholder="Class/Declination",
                classes="input",
                id="input-class_decl",
            ),
            Label("Root:", classes="label"),
            Input(
                value=None,
                placeholder="Root",
                classes="input",
                id="input-root",
            ),
            Static(),
            Button("Search", variant="success", id="search"),
            Button("Cancel", variant="warning", id="back"),
            id="input-dialog",
        )

        self.linel_list = DataTable(classes="Words-list")
        self.linel_list.focus()
        self.linel_list.add_columns("ID","Word", "Type", "English", "Class/Declinations", "Root", "Notes")
        self.linel_list.cursor_type = "row"
        self.linel_list.zebra_stripes = True

        yield Horizontal(self.linel_list)

        yield Footer()

        
    @on(Button.Pressed, "#search")
    def action_search(self):
        words_list = self.query_one(DataTable)
        words_list.clear()
        word = self.query_one("#input-word", Input).value
        type = self.query_one("#input-type", Input).value
        english = self.query_one("#input-english", Input).value
        class_decl = self.query_one("#input-class_decl", Input).value
        root = self.query_one("#input-root", Input).value
        words = self.db.query_words(word, type, english, class_decl, root)
        
        for word_data in words:
            words_list.add_row(*word_data[0:])

class CSVSelectionScreen(Screen):

    def __init__(self, db):
        super().__init__()
        self.db = db

    def compose(self):

        csv_dir = pathlib.Path(__file__).parent / "database"
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]

        if not csv_files:
            yield Label("No CSV found in the 'database' folder.")
            yield Button("Cancel", id="cancel")
        else:
            yield Label("Select a csv to load:")
            self.selection = Select.from_values(csv_files)
            yield self.selection

            yield Button("Load", id="load")
            yield Button("Cancel", id="back")     

    @on(Button.Pressed, "#load")
    def action_load(self):
        selected_csv = self.selection.value
    
        if not selected_csv == Select.BLANK:
            csv_path = pathlib.Path(__file__).parent / "database" / selected_csv
            with open(csv_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                records = [row for row in reader]

                for record in records:
                    word = record.get("word")
                    type = record.get("type")
                    english = record.get("english")
                    class_decl = record.get("class_decl")
                    root = record.get("root")
                    notes = record.get("notes")

                    added_word = (word, type, english, class_decl, root, notes)
                    self.db.add_word(added_word)

            self.app.switch_to_home()
        else:
            print("No CSV selected")


class WordGeneratorScreen(Screen):

    def __init__(self):
        super().__init__()
        self.phon = {}
        self.syl = []
        self.load_default_patterns()


    def load_default_patterns(self):
        base_dir = pathlib.Path(__file__).parent / "phonology"
        sounds_file = base_dir / "sounds.txt"
        syllables_file = base_dir / "syllables.txt"

        if sounds_file.exists():
            with open(sounds_file, "r") as f:
                self.default_sounds = f.read()
        else:
            self.default_sounds = ""

        if syllables_file.exists():
            with open(syllables_file, "r") as f:
                self.default_syllables = f.read()
        else:
            self.default_syllables = ""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Number of Words to Generate:")
        self.num_input = Input(placeholder="Enter a number", id="num_input")
        yield self.num_input

        yield Label("Phonological Categories (sounds.txt):")
        self.sounds_input = TextArea(text=self.default_sounds, id="sounds_input")
        yield self.sounds_input

        yield Label("Syllable Structures (syllables.txt):")
        self.syllables_input = TextArea(text=self.default_syllables, id="syllables_input")
        yield self.syllables_input

        yield Button("Generate Words", id="generate")

        self.output = TextArea(read_only=True, id="output")
        yield Label("Generated Words:")
        yield self.output

        yield Footer()

    def load_patterns(self):
        ph = self.sounds_input.text.splitlines()
        syl = self.syllables_input.text.splitlines()

        for cat in ph:
            phrase = cat.split("=")
            if len(phrase) == 2:
                self.phon[phrase[0]] = phrase[1].split(",")

        self.syl = syl

    def generate_words(self):
        num_words = int(self.num_input.value or 10)

        words = [self.gen_word() for _ in range(num_words)]
        self.output.text = "\n".join(words)

    def gen_word(self):
        structure = random.choice(self.syl)
        sounds = [random.choice(self.phon[category]) for category in structure]
        return "".join(sounds)

    @on(Button.Pressed, "#generate")
    def action_generate(self):
        if self.sounds_input.text and self.syllables_input.text:
            self.load_patterns()
            self.generate_words()
        else:
            self.output.text = "Please provide content for both sounds and syllables."