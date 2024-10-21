from textual.app import App, on
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, DataTable, Static, Input

class LinelApp(App):
    CSS_PATH = "linel.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Toggle dark mode"),
        ("a", "add", "Add"),
        ("d", "delete", "Delete"),
        ("q", "request_quit", "Quit"),  
    ]
    
    def __init__(self, db):
        super().__init__()
        self.db = db

    def compose(self):
        yield Header()
        linel_list = DataTable(classes="Words-list")
        linel_list.focus()
        linel_list.add_columns("Word", "Type", "English", "Class/Declinations", "Root", "Notes")
        linel_list.cursor_type = "row"
        linel_list.zebra_stripes = True
        add_button = Button("Add", variant="success", id="add")
        add_button.focus()
        buttons_panel = Vertical(
            add_button,
            Button("Delete", variant="warning", id="delete"),
            Static(classes="separator"),
            classes="buttons-panel",
        )
        yield Horizontal(linel_list, buttons_panel)
        yield Footer()

    def on_mount(self):
        self.title = "LINEL"
        self.sub_title = "A Conlang Tool"
        self._load_words()

    def _load_words(self):
        words_list = self.query_one(DataTable)
        for word_data in self.db.get_all_words():
            id, *word = word_data
            words_list.add_row(*word, key=id)


    def action_toggle_dark(self):
        self.dark = not self.dark

    def action_request_quit(self):
        def check_answer(accepted):
            if accepted:
                self.exit()
        self.push_screen(QuestionDialog("Do you want to quit?"), check_answer)

    @on(Button.Pressed, "#add")
    def action_add(self):
        def check_word(word_data):
            if word_data:
                self.db.add_word(word_data)
                id, *word = self.db.get_last_word()
                self.query_one(DataTable).add_row(*word, key=id)

        self.push_screen(InputDialog(), check_word)

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
        self.push_screen(
            QuestionDialog(f"Do you want to delete {word}?"),
            check_answer,
        )

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

class InputDialog(Screen):
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
            Button("Cancel", variant="warning", id="cancel"),
            Button("Ok", variant="success", id="ok"),
            id="input-dialog",
        )

    def on_button_pressed(self, event):
        if event.button.id == "ok":
            word = self.query_one("#word", Input).value
            type = self.query_one("#type", Input).value
            english = self.query_one("#english", Input).value
            class_decl = self.query_one("#class_decl", Input).value
            root = self.query_one("#root", Input).value
            notes = self.query_one("#notes", Input).value
            self.dismiss((word, type, english, class_decl, root, notes))
        else:
            self.dismiss()