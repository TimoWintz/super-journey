import gi, sys, repository
gi.require_version('Gtk', '3.0')

import handler # import MainWindowHandler, ApplicationHeaderHandler
from gi.repository import Gtk, GObject



def main(args):
    GObject.threads_init()
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
    