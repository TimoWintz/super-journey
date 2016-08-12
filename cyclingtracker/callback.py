class ActivitiesLoadedHandler:
    def on_activities_loaded(self, activities):
        raise NotImplementedError

class ActivityImportedHandler:
    def on_activity_imported(self, activity = None, problem = None):
        raise NotImplementedError

class ActivityDeletedHandler:
    def on_activity_deleted(self, activity):
        raise NotImplementedError

class SlowMethodArgs:
    def __init__(self):
        return

class ImportActivityMethodArgs(SlowMethodArgs):
    def __init__(self, file_name, file_type):
        self.file_name = file_name
        self.file_type = file_type
