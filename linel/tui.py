from linel.database import Database
from textual.app import App, on, ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, DataTable, Static, Input, Select, TextArea
import pathlib, os, random

class DatabaseSelectionScreen(Screen):

    def __init__(self):
        super().__init__()

    def compose(self):

        database_dir = pathlib.Path(__file__).parent / "database"
        db_files = [f for f in os.listdir(database_dir) if f.endswith(".db")]

        if not db_files:
            yield Label("No databases found in the 'database' folder.")
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
    
        if selected_db:
            db_path = pathlib.Path(__file__).parent / "database" / selected_db
            self.app.db_path = db_path
            self.app.push_screen(Home(db_path=db_path))
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
        super.__init__()

    def compose(self):
        ...

class Home(Screen):

    BINDINGS = [("a", "add", "Add word"),
                ("u", "modify", "Update word"),
                ("d","delete", "Delete word")]

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    def compose(self):
        yield Header()
        self.linel_list = DataTable(classes="Words-list")
        self.linel_list.focus()
        self.linel_list.add_columns("ID","Word", "Type", "English", "Class/Declinations", "Root", "Notes")
        self.linel_list.cursor_type = "row"
        self.linel_list.zebra_stripes = True
        add_button = Button("Add", variant="success", id="add")
        modify_button = Button("Modify", variant="success", id="modify")
        delete_button = Button("Delete", variant="warning", id="delete")
        add_button.focus()
        buttons_panel = Vertical(
            add_button,
            modify_button,
            delete_button,
            Static(classes="separator"),
            classes="buttons-panel",
        )
        yield Horizontal(self.linel_list, buttons_panel)
        yield Footer()

    def on_mount(self):
        self.db = Database(db_path=self.db_path)
        self._load_words()

    def _load_words(self):
        words_list = self.query_one(DataTable)
        words_list.clear()
        words = self.db.get_all_words()
    
        for word_data in words:
            word_id = word_data[0]  # Supponiamo che il primo elemento sia l'ID
            if word_id:
                words_list.add_row(word_id, *word_data[1:], key=str(word_id))
            else:
                print(f"Invalid word ID: {word_id} for word: {word_data}")

    @on(Button.Pressed, "#add")
    def action_add(self):
        def check_word(word_data):
            if word_data:
                self.db.add_word(word_data)
                id, *word = self.db.get_last_word()
                self.query_one(DataTable).add_row(*word, key=id)

        self.app.push_screen(AddDialog(), check_word)

    @on(Button.Pressed, "#modify")
    def action_modify(self):
        words_list = self.query_one(DataTable)
        
        # Recupera la chiave della riga selezionata
        row_key, _ = words_list.coordinate_to_cell_key(words_list.cursor_coordinate)
        
        if not row_key:
            print("No row selected")
            return  # Nessuna riga selezionata

        # Recupera i dati della riga selezionata
        word_data = words_list.get_row(row_key)
        
        if not word_data:
            print(f"No data found for the selected row {row_key}")
            return

        # Mostra il dialogo di modifica con i dati esistenti
        word_id = row_key.value
        word_record = self.db.get_word_by_id(int(word_id))

        def handle_update(updated_word):
            if updated_word:
                self.db.update_word(word_id, updated_word)
                self._load_words()
        
        # Mostra la schermata del dialogo e gestisce l'aggiornamento
        self.app.push_screen(UpdateDialog(word_record), handle_update)


    @on(Button.Pressed, "#delete")
    def action_delete(self):
        words_list = self.query_one(DataTable)
        row_key, _ = words_list.coordinate_to_cell_key(
            words_list.cursor_coordinate
        )

        def check_answer(accepted):
            if accepted and row_key:
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
        self.db_path = None  # Inizializza db_path come None

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
        no_button = Button("No", variant="primary", id="no")
        no_button.focus()

        yield Grid(
            Label(self.message, id="question"),
            Button("Yes", variant="error", id="yes"),
            no_button,
            id="question-dialog",
        )

    def on_button_pressed(self, event):
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

class AddDialog(Screen):
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
            Button("Cancel", variant="warning", id="cancel"),
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

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss(None)


class UpdateDialog(Screen):

    def __init__(self, word_record):
        super().__init__()
        self.word_record = word_record  # Passiamo i dati esistenti da modificare

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
            Button("Cancel", variant="warning", id="cancel"),
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
        
        self.dismiss(updated_word)  # Chiude il dialogo e ritorna i nuovi dati

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss(None)

class WordGeneratorScreen(Screen):

    def __init__(self):
        super().__init__()
        self.phon = {}
        self.syl = []
        self.load_default_patterns()


    def load_default_patterns(self):
        """Carica i contenuti predefiniti dei file sounds.txt e syllables.txt."""
        base_dir = pathlib.Path(__file__).parent / "phonology"
        sounds_file = base_dir / "sounds.txt"
        syllables_file = base_dir / "syllables.txt"

        # Leggi sounds.txt
        if sounds_file.exists():
            with open(sounds_file, "r") as f:
                self.default_sounds = f.read()  # Salva il contenuto per TextArea
        else:
            self.default_sounds = ""

        # Leggi syllables.txt
        if syllables_file.exists():
            with open(syllables_file, "r") as f:
                self.default_syllables = f.read()  # Salva il contenuto per TextArea
        else:
            self.default_syllables = ""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Number of Words to Generate:")
        self.num_input = Input(placeholder="Enter a number", id="num_input")
        yield self.num_input

        # Campo di testo per incollare il contenuto di sounds.txt
        yield Label("Phonological Categories (sounds.txt):")
        self.sounds_input = TextArea(text=self.default_sounds, id="sounds_input")
        yield self.sounds_input

        # Campo di testo per incollare il contenuto di syllables.txt
        yield Label("Syllable Structures (syllables.txt):")
        self.syllables_input = TextArea(text=self.default_syllables, id="syllables_input")
        yield self.syllables_input

        yield Button("Generate Words", id="generate")

        # Area di testo per visualizzare le parole generate
        self.output = TextArea(read_only=True, id="output")
        yield Label("Generated Words:")
        yield self.output

        yield Footer()

    def load_patterns(self):
        """Carica i pattern dalle aree di testo."""
        ph = self.sounds_input.text.splitlines()
        syl = self.syllables_input.text.splitlines()

        # Popola il dizionario `phon` con le categorie e i suoni
        for cat in ph:
            phrase = cat.split("=")
            if len(phrase) == 2:
                self.phon[phrase[0]] = phrase[1].split(",")

        self.syl = syl

    def generate_words(self):
        """Genera le parole in base ai pattern."""
        num_words = int(self.num_input.value or 10)  # Default to 10 if input is empty

        words = [self.gen_word() for _ in range(num_words)]
        self.output.text = "\n".join(words)  # Visualizza le parole generate

    def gen_word(self):
        """Genera una parola singola usando il pattern di `phon` e `syl`."""
        structure = random.choice(self.syl)
        sounds = [random.choice(self.phon[category]) for category in structure]
        return "".join(sounds)

    @on(Button.Pressed, "#generate")
    def action_generate(self):
        """Genera le parole in base ai dati inseriti."""
        if self.sounds_input.text and self.syllables_input.text:
            self.load_patterns()
            self.generate_words()
        else:
            self.output.text = "Please provide content for both sounds and syllables."