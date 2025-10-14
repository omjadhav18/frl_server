from django.urls import path
from .views import *

urlpatterns = [
    path("upload/", QTableUploadView.as_view(), name="upload-qtable"),
    path("list/", ListQTablesView.as_view(), name="list-qtables"), 
    path("aggregate/", AggregateQTablesView.as_view(), name="aggregate"),     # ADMIN
    path("global/", GetGlobalQTableView.as_view(), name="get-global-qtable"),
    path("progress/<uuid:car_id>/", CarTrainingProgressView.as_view(), name="car-progress"),
    path("global-history/", GlobalModelHistoryView.as_view(), name="global-history"),
    path("control/start_training/", StartTrainingView.as_view(), name="start-training"),
    path("control/stop_training/", StopTrainingView.as_view(), name="stop-training"),
    path("control/start_test/", StartTestView.as_view(), name="start-test"),
    path("control/global_available/", GlobalAvailableView.as_view(), name="global-available"),
    path("cli-events/", ClientEventLogListView.as_view(), name="event-log-list"),
    path("test-results/", TestResultUploadView.as_view(), name="test-results"),
    path("test-results/<uuid:run_id>/", TestResultSummaryView.as_view(), name="test-summary"),

    #admindash apis
    path("client-qtables/", ClientQTableListView.as_view(), name="client-qtable-list"),
    path("global-qtables/", GlobalQTableListView.as_view(), name="global-qtable-list"),
    path("list/test-results/", TestResultListView.as_view(), name="test-result-list"),
    path('evaluate/global-qtables/', EvaluateAllGlobalQTablesView.as_view(), name='evaluate_all_global_qtables'),
    path("runs/", FederatedRunListView.as_view(), name="federated-run-list"),
    path("events/", ClientEventLogListView.as_view(), name="client-event-log-list"),
    path("summary/counts/", FederatedSummaryCountView.as_view(), name="federated-summary-counts"),


]