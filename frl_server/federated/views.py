from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from accounts.permissions import IsCarUser
from .models import *
from .serializers import *
from rest_framework import generics
from accounts.permissions import IsAdminUser
from rest_framework import status
import numpy as np
from .utils import *
import json, random, time


# class UploadQTableView(APIView):
#     permission_classes = [IsAuthenticated, IsCarUser]

#     def post(self, request, *args, **kwargs):
#         q_table = request.data.get("q_table")
#         track_id = request.data.get("track_id")
#         episode = request.data.get("episode", 0)
#         reward_score = request.data.get("reward_score", 0.0)

#         if not q_table:
#             return Response({"error": "q_table is required"}, status=400)

#         qtable_instance = QTable.objects.create(
#             car=request.user,
#             track_id=track_id,
#             episode=episode,
#             reward_score=reward_score,
#             q_table=q_table
#         )

#         serializer = QTableSerializer(qtable_instance)
#         return Response({
#             "message": "Q-table uploaded successfully",
#             "q_table": serializer.data
#         }, status=201)

#this was working just not have global q table save after aggregation
# class QTableUploadView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         run_id = request.data.get("run_id")
#         q_table = request.data.get("q_table")

#         client_q = ClientQTable.objects.create(
#             client=request.user,
#             run_id=run_id,
#             q_table=q_table
#         )

#         # Example: trigger aggregation if enough clients uploaded
#         uploaded_count = ClientQTable.objects.filter(run_id=run_id).count()
#         if uploaded_count >= 2:  # change threshold as needed
#             global_q = aggregate_qtables(run_id)
#             if global_q:
#                 broadcast_new_global(global_q)

#         return Response({"status": "uploaded"}, status=201)
    
class QTableUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        run_id = request.data.get("run_id")
        q_table = request.data.get("q_table")

        # Save client Q-table
        client_q = ClientQTable.objects.create(
            client=request.user,
            run_id=run_id,
            q_table=q_table
        )

        # Count uploads for this run
        # uploaded_count = ClientQTable.objects.filter(run_id=run_id).count()

        # # Trigger aggregation if enough clients uploaded
        # if uploaded_count >= 2:  # ✅ threshold can be tuned
        #     aggregated = aggregate_qtables(run_id)
        #     if aggregated:
        #         # Save into GlobalQTable
        #         global_q = GlobalQTable.objects.create(
        #             q_table=aggregated,
        #             performance_score=0.0  # you can compute something later
        #         )

        return Response({"status": "uploaded"}, status=201)

class AggregateQTablesView(APIView):
    """
    Admin-only endpoint to aggregate all client Q-tables (no run filter).
    """
    # permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Fetch all client Q-tables
        client_qtables = ClientQTable.objects.all()
        if not client_qtables.exists():
            return Response({"error": "No client Q-tables found"}, status=404)

        # Extract q_table dicts
        qtables = [q.q_table for q in client_qtables]

        # Aggregate Q-tables
        try:
            aggregated_q = aggregate_qtables(qtables)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        # Save into GlobalQTable
        global_q = GlobalQTable.objects.create(
            q_table=aggregated_q,
            performance_score=0.0  # can be updated later
        )

        return Response({"status": "aggregated", "global_q_id": global_q.id}, status=201)


#use this if qtable is sent as a dictionary
# import json, ast

# class QTableUploadView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         run_id = request.data.get("run_id")
#         q_table_raw = request.data.get("q_table")

#         try:
#             # Parse JSON back
#             q_dict = json.loads(q_table_raw)

#             # Convert "(0, 1)" → (0, 1) tuples
#             q_dict = {ast.literal_eval(k): v for k, v in q_dict.items()}

#         except Exception as e:
#             return Response({"error": f"Invalid Q-table format: {e}"}, status=400)

#         # Store the raw string or the parsed dict (depending on your model field type)
#         client_q = ClientQTable.objects.create(
#             client=request.user,
#             run_id=run_id,
#             q_table=q_table_raw  # keep original JSON string
#         )

#         # ✅ Pass normalized dict to aggregator
#         uploaded_count = ClientQTable.objects.filter(run_id=run_id).count()
#         if uploaded_count >= 2:  # threshold
#             global_q = aggregate_qtables(run_id)
#             if global_q:
#                 broadcast_new_global(global_q)

#         return Response({"status": "uploaded"}, status=201)


class ListQTablesView(generics.ListAPIView):
    queryset = QTable.objects.all().order_by("-created_at")
    serializer_class = QTableSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


# class AggregateQTablesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        # Get all client Q-tables
        client_qtables = QTable.objects.all()
        if not client_qtables.exists():
            return Response({"error": "No client Q-tables available"}, status=status.HTTP_400_BAD_REQUEST)

        qtables = [q.q_table for q in client_qtables]

        try:
            aggregated = aggregate_qtables(qtables)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        new_score = evaluate_qtable(aggregated)

        # Compare with existing global
        latest_global = GlobalQTable.objects.order_by("-aggregated_at").first()
        if latest_global is None or new_score > latest_global.performance_score:
            GlobalQTable.objects.create(q_table=aggregated, performance_score=new_score)
            message = "Global Q-table updated"
        else:
            message = "New aggregation discarded (not better than current global)"

        return Response({"message": message, "new_score": new_score}, status=status.HTTP_200_OK)


# class GetGlobalQTableView(APIView):
#     # permission_classes = [IsAuthenticated]

#     def get(self, request):
#         global_q = GlobalQTable.objects.order_by("-aggregated_at").first()
#         if not global_q:
#             return Response({"error": "No global Q-table available"}, status=status.HTTP_404_NOT_FOUND)

#         return Response({
#             "q_table": global_q.q_table,
#             "performance_score": global_q.performance_score,
#             "aggregated_at": global_q.aggregated_at
#         })
    
class GetGlobalQTableView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        global_q = GlobalQTable.objects.order_by("-performance_score").first()
        if not global_q:
            return Response({"error": "No global Q-table available"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "q_table": global_q.q_table,
            "performance_score": global_q.performance_score,
            "aggregated_at": global_q.aggregated_at
        })

class CarTrainingProgressView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, car_id):
        qtables = QTable.objects.filter(car__id=car_id).order_by("episode", "created_at")
        serializer = QTableSerializer(qtables, many=True)
        return Response(serializer.data)


class GlobalModelHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        globals = GlobalQTable.objects.all().order_by("aggregated_at")
        data = [
            {
                "id": g.id,
                "performance_score": g.performance_score,
                "aggregated_at": g.aggregated_at,
            }
            for g in globals
        ]
        return Response(data)


# class StartTrainingView(APIView):
#     # permission_classes = [IsAdminUser]

#     def post(self, request, *args, **kwargs):
#         broadcast_to_clients("start_training", {"msg": "Begin training"})
#         return Response({"status": "Training started"})

class StartTrainingView(APIView):
    # permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        from .models import FederatedRun

        # 1. Create a new federated run
        run = FederatedRun.objects.create()

        # 2. Broadcast start_training with the real run_id
        data = {
            "run_id": str(run.id),  # ✅ actual UUID
            "episodes": request.data.get("episodes", 5),
            "steps": request.data.get("steps", 5),
        }
        broadcast_to_clients("start_training", data)

        return Response({
            "status": "Training started",
            "run_id": str(run.id)
        })


class StopTrainingView(APIView):
    # permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        broadcast_to_clients("stop_training", {"msg": "Stop training"})
        return Response({"status": "Training stopped"})

# class StartTestView(APIView):
#     permission_classes = [IsAdminUser]

#     def post(self, request, *args, **kwargs):
#         broadcast_to_clients("start_test", {"msg": "Switch to test mode"})
#         return Response({"status": "Test mode started"})

class StartTestView(APIView):
    # permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        test_episodes = request.data.get("test_episodes", 10)  # default = 10

        broadcast_to_clients("start_test", {
            "msg": "Switch to test mode",
            "test_episodes": test_episodes,
        })

        return Response({
            "status": "Test mode started",
            "test_episodes": test_episodes
        })


class GlobalAvailableView(APIView):
    # permission_classes = [IsAdminUser]  # uncomment if only admins can trigger

    def post(self, request, *args, **kwargs):
        # Simply trigger broadcast, no need for global_id
        broadcast_to_clients("new_global_available", None)

        return Response({
            "status": "New global model broadcasted"
        }, status=200)


    
class ClientEventLogListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ClientEventLogSerializer
    queryset = ClientEventLog.objects.all().order_by("-timestamp")


class TestResultUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        run_id = request.data.get("run_id")
        episodes = request.data.get("episodes")
        success_rate = request.data.get("success_rate")
        avg_reward = request.data.get("avg_reward")

        result = TestResult.objects.create(
            client=request.user,
            run_id=run_id,
            episodes=episodes,
            success_rate=success_rate,
            avg_reward=avg_reward,
        )

        return Response({"status": "uploaded", "id": str(result.id)}, status=201)


class TestResultSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, run_id, *args, **kwargs):
        results = TestResult.objects.filter(run_id=run_id)

        summary = {
            "count": results.count(),
            "avg_success_rate": results.aggregate(models.Avg("success_rate"))["success_rate__avg"],
            "avg_reward": results.aggregate(models.Avg("avg_reward"))["avg_reward__avg"],
            "details": [
                {
                    "client": r.client.username,
                    "episodes": r.episodes,
                    "success_rate": r.success_rate,
                    "avg_reward": r.avg_reward,
                }
                for r in results
            ]
        }
        return Response(summary)


class ClientQTableListView(generics.ListAPIView):
    """
    List all Q-tables uploaded by clients.
    """
    queryset = ClientQTable.objects.all().order_by("-uploaded_at")
    serializer_class = ClientQTableSerializer
    permission_classes = [AllowAny]  # Only admins can see



class GlobalQTableListView(generics.ListAPIView):
    """
    List all global Q-tables.
    """
    queryset = GlobalQTable.objects.all().order_by("-aggregated_at")  # latest first
    serializer_class = GlobalQTableSerializer
    permission_classes = [AllowAny]  # only admin can access


class TestResultListView(generics.ListAPIView):
    queryset = TestResult.objects.all().order_by("-uploaded_at")
    serializer_class = TestResultSerializer
    permission_classes = [AllowAny]


class EvaluateAllGlobalQTablesView(APIView):
    """
    Simulate car testing for ALL GlobalQTable entries and update each one's performance_score.
    No GPIO — purely simulated environment.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            global_q_tables = GlobalQTable.objects.all().order_by("-aggregated_at")
            if not global_q_tables.exists():
                return Response({"error": "No global Q-tables found"}, status=404)

            results = []

            # --- Simulation parameters ---
            states = [(0, 0), (1, 0), (0, 1), (1, 1)]
            actions = [0, 1]  # 0=Forward, 1=Backward
            test_episodes = 5
            steps = 5

            # --- Loop through each global Q-table ---
            for global_q in global_q_tables:
                q_table = json.loads(global_q.q_table) if isinstance(global_q.q_table, str) else global_q.q_table

                total_reward = 0
                success_count = 0

                for ep in range(test_episodes):
                    state = random.choice(states)
                    ep_reward = 0

                    for _ in range(steps):
                        # Greedy action (use max Q-value)
                        action = max(q_table[str(state)], key=q_table[str(state)].get)
                        next_state = random.choice(states)

                        # Reward logic (same as client side)
                        front, back = state
                        if action == "0" or action == 0:
                            reward = -10 if front == 1 else +5
                        else:
                            reward = -10 if back == 1 else +5

                        ep_reward += reward
                        if reward > 0:
                            success_count += 1

                        state = next_state
                        time.sleep(0.05)

                    total_reward += ep_reward

                avg_reward = total_reward / test_episodes
                success_rate = (success_count / (test_episodes * steps)) * 100
                performance_score = round((avg_reward + success_rate / 10), 2)

                # --- Update performance score ---
                global_q.performance_score = performance_score
                global_q.save()

                results.append({
                    "id": str(global_q.id),
                    "avg_reward": avg_reward,
                    "success_rate": success_rate,
                    "performance_score": performance_score,
                    "aggregated_at": global_q.aggregated_at
                })

            return Response({
                "message": f"✅ Evaluated {len(results)} Global Q-tables successfully.",
                "results": results
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

class FederatedRunListView(generics.ListAPIView):
    queryset = FederatedRun.objects.all().order_by("-started_at")
    serializer_class = FederatedRunSerializer
    permission_classes = [AllowAny]


class ClientEventLogListView(generics.ListAPIView):
    queryset = ClientEventLog.objects.all().order_by("-timestamp")
    serializer_class = ClientEventLogSerializer
    permission_classes = [AllowAny]

class FederatedSummaryCountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            "federated_runs": FederatedRun.objects.count(),
            "client_qtables": ClientQTable.objects.count(),
            "global_qtables": GlobalQTable.objects.count(),
            "test_results": TestResult.objects.count(),
        }
        return Response(data, status=status.HTTP_200_OK)