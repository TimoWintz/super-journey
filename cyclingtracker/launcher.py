import gi
gi.require_version('GtkClutter', '1.0')
from gi.repository import GtkClutter
gi.require_version('Gtk', '3.0')
from gi.repository import GtkClutter
from gi.repository import Gtk, GObject, Gdk
import sys, repository, handler

def main(args):
    GObject.threads_init()
    GtkClutter.init([])
    repo = repository.Repository()
    repo.init_database()
    if len(args) > 1 and args[1] == "populate":
        repo.populate_activities()
    main_window_handler = handler.MainWindowHandler(repo)
    main_window = main_window_handler.build_view()

    header_handler = handler.ApplicationHeaderHandler(repo, main_window_handler)
    header = header_handler.build_view()
    main_window.set_titlebar(header)
    main_window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main(sys.argv)
    