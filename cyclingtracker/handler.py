import gi, callback
from gi.repository import GObject, Gtk, Gio, GLib, Gdk
gi.require_version('OsmGpsMap', '1.0')
from gi.repository import OsmGpsMap
from repository import Repository, FileType

class GladeHandler(object):
    """
    Generic class to generate and handle UI elements and signals from Glade.
    Subclasses will contain signal handling and UI manipulation.
    Slow operations should be run through `execute_slow_method()`
    UI shall only be manipulated within a call to `run_update_ui()`.
    """

    def __init__(self, repository, glade_file_name, object_name):
        """
        """
        self.repository = repository
        self.glade_file_name = glade_file_name
        self.object_name = object_name

    def build_view(self):
        """
        Builds the view from the glade template given at initialization
        and connects its signals it to `self`
        """
        self.builder = Gtk.Builder()
        self.builder.add_from_file("glade/" + self.glade_file_name)
        self.builder.connect_signals(self)
        return self.get_object()

    def get_object(self):
        """
        Returns the object relevant to `self` (i.e. top-level container)
        """
        return self.builder.get_object(self.object_name)

    def get_object_by_name(self, object_name):
        """
        Returns the child object named `object_name`
        """
        return self.builder.get_object(object_name)
    
    def execute_slow_method(self, method, args = None, callback_handler = None):
        """
        Executes `method` as a GTK-friendly background task.
        Arguments are passed to the method through `args`.
        Backgound method can be given a `callback` that can be called
        upon completion
        """
        Gio.io_scheduler_push_job(self._dispatch_method,
            [method, args, callback_handler], GLib.PRIORITY_DEFAULT, None)
    
    def _dispatch_method(self, job, cancellable, method_data):
        """
        (Private) dispatches args and callback to the correct method, to match
        signature as `method(args, callback)` i.e. in `Repository`
        """
        to_call = method_data[0]
        args = method_data[1]
        callback_handler = method_data[2]
        to_call(args, callback_handler)

    def run_update_ui(self, method, args = None):
        """
        Ececutes a UI-modifying method in a GTK-friendly manner
        """
        if args:
            GLib.idle_add(method, args)
        else:
            GLib.idle_add(method)

class ApplicationHeaderHandler(GladeHandler, callback.ActivityImportedHandler):
    """
    Handler class for the Header Bar
    """

    def __init__(self, repository, main_window_handler):
        super().__init__(repository, "applicationHeaderBar.glade", "ApplicationHeaderBar")
        self.window_handler = main_window_handler

    def on_import_click(self, *args):
        dialog = Gtk.FileChooserDialog("Choisir une activité à importer", self.window_handler.get_object(),
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_fit = Gtk.FileFilter()
        filter_fit.set_name("Garmin FIT")
        filter_fit.add_pattern("*.fit")

        filter_gpx = Gtk.FileFilter()
        filter_gpx.set_name("GPX")
        filter_gpx.add_pattern("*.gpx")

        dialog.add_filter(filter_gpx)
        dialog.add_filter(filter_fit)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_name = dialog.get_filename()
            file_type = None
            filter = dialog.get_filter()
            if filter == filter_fit:
                file_type = FileType.fit
            elif filter == filter_gpx:
                file_type = FileType.gpx
            self.import_activity(file_name, file_type)

        dialog.destroy()

    def import_activity(self, filename, filetype):
        args = callback.ImportActivityMethodArgs(filename, filetype)
        self.run_update_ui(self.window_handler.activities_tab_handler.add_spinner)
        self.execute_slow_method(self.repository.import_activity, args, self)
    
    def on_activity_imported(self, activity=None, problem=None):
        if problem:
            self.run_update_ui(self.show_error_dialog, problem)
        else:
            self.window_handler.activities_tab_handler.add_activity(activity)
    
    def show_error_dialog(self, problem):
        self.window_handler.activities_tab_handler.hide_spinner()
        dialog = Gtk.MessageDialog(self.window_handler.get_object(), 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK, "Une erreur est survenue à l'importation")
        dialog.format_secondary_text(problem)
        dialog.run()
        dialog.destroy()

class MainWindowHandler(GladeHandler):
    """
    Handler class for the Main Window. Initializes the tabs through their handlers
    upon realization (i.e. construction of the main window elements).
    Exits GTK loop on window close.
    """

    def __init__(self, repository):
        super().__init__(repository, "mainWindow.glade", "MainApplicationWindow")
        self.activities_tab_handler = None

    def on_destroy(self, *args):
        """
        Tells GTK to exit the main loop
        """
        Gtk.main_quit(*args)

    def on_realize(self, *args):
        self.activities_tab_handler = ActivitiesTabHandler(self.repository)
        self.activities_tab_handler.build_view()
        activities_paned = self.activities_tab_handler.get_object()
        self.get_object_by_name("ActivitiesTabBox").add(activities_paned)

class ActivitiesTabHandler(GladeHandler, callback.ActivitiesLoadedHandler, callback.ActivityDeletedHandler):
    """
    Handler class for the 'Activities' tab (`ActivitiesPaned` in Glade).
    Has a spinner whislt no data is loaded.
    Loads activities from database on realize and then feeds the list with
    activities (filtering out the spinner row).
    Displays selected activity in the right pane.
    """
    def __init__(self, repository):
        super().__init__(repository, "activitiesPaned.glade", "ActivitiesPaned")
        self.activity_rows_to_lih = dict()
        self.activities = []
        self.displayed_activity = None
        self.activity_details_handler = None

    def hide_spinner(self):
        list_box = self.get_object_by_name("ActivitiesListBox")
        list_box.set_filter_func(self.filter_func, False)

    def add_spinner(self):
        list_box = self.get_object_by_name("ActivitiesListBox")
        list_box.set_filter_func(lambda row: True)
        sih = ActivitySpinnerItemHandler(self.repository)
        sih.build_view()
        spinner_row = sih.get_object()
        list_box.add(spinner_row)
    
    def filter_func(self, row, show_spinner):
        if show_spinner and row not in self.activity_rows_to_lih:
            return True
        if row in self.activity_rows_to_lih and not show_spinner:
            return True
        else:
            return False

    def on_realize(self, *args):
        self.add_spinner()
        self.fetch_activities()
    
    def on_activities_loaded(self, activities):
        self.activities = activities
        self.run_update_ui(self.update_list_view)
    
    def on_row_selected(self, list_box, list_box_row):
        if list_box_row:
            lih = self.activity_rows_to_lih[list_box_row]
            self.displayed_activity = lih.activity_data
        self.update_activity_view()

    def on_delete_clicked(self, *args):
        self.execute_slow_method(self.repository.delete_activity, self.displayed_activity, self)

    def on_activity_deleted(self, activity):
        self.displayed_activity = None
        self.activities.remove(activity)
        self.run_update_ui(self.update_activity_view)
        self.run_update_ui(self.update_list_view)

    def fetch_activities(self):
        self.execute_slow_method(self.repository.get_all_activities, None, self)

    def add_activity(self, activity):
        self.activities.append(activity)
        self.run_update_ui(self.update_list_view)

    def update_activity_view(self):
        box = self.get_object_by_name("ActivityDetailsPaneBox")
        button_delete = self.get_object_by_name("DeleteActivityButton")

        if self.activity_details_handler:
            box.remove(self.activity_details_handler.get_object())

        if self.displayed_activity:
            self.activity_details_handler = ActivityDetailsHandler(self.repository, self.displayed_activity)
            adb = self.activity_details_handler.build_view()
            box.add(adb)
            box.show_all()
            button_delete.set_visible(True)
        else:
            button_delete.set_visible(False)

    def update_list_view(self):
        self.empty_list_box()
        list_box = self.get_object_by_name("ActivitiesListBox")
        for activity in self.activities:
            lih = ActivityListItemHandler(self.repository, activity)
            list_box_row = lih.build_view()
            self.activity_rows_to_lih[list_box_row] = lih
            list_box.add(list_box_row)
            if self.displayed_activity and self.displayed_activity.id == activity.id:
                list_box.select_row(list_box_row)
        self.hide_spinner()

    def empty_list_box(self):
        list_box = self.get_object_by_name("ActivitiesListBox")
        list_box.bind_model(None, None, None)
        self.activity_rows_to_lih = dict()

class ActivityListItemHandler(GladeHandler):
    def __init__(self, repository, activity_data):
        super().__init__(repository, "activityListBoxRow.glade", "ActivityListBoxRow")
        self.activity_data = activity_data

    def build_view(self):
        res = super().build_view()
        label = self.get_object_by_name("ActivityNameLabel")
        label.set_label(self.activity_data.name)
        return res

    def get_activity_data(self):
        return self.activity_data

class ActivitySpinnerItemHandler(GladeHandler):
    def __init__(self, repository):
        super().__init__(repository, "spinnerListBoxRow.glade", "SpinnerListBoxRow")

class ActivityDetailsHandler(GladeHandler):
    def __init__(self, repository, activity_data):
        super().__init__(repository, "activityDetailsBox.glade", "ActivityDetailsBox")
        self.activity_data = activity_data
    
    def build_view(self):
        res = super().build_view()
        label = self.get_object_by_name("ActivityDetailsLabel")
        label.set_markup(self.activity_data.to_markup())
        map = OsmGpsMap.Map(repo_uri='http://a.tile.opencyclemap.org/cycle/#Z/#X/#Y.png')
        map.set_vexpand(True)
        
        track = OsmGpsMap.MapTrack()
        last_point = None

        # add the activity's track
        for gps_point in self.activity_data.gps_track.gps_points:
            point = OsmGpsMap.MapPoint()
            point.set_degrees(gps_point.latitude, gps_point.longitude)
            track.add_point(point)
            last_point = gps_point
        map.track_add(track)
        map.set_center_and_zoom(last_point.latitude, last_point.longitude, 13)
        res.add(map)
        return res