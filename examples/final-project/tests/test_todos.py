# tests/test_todos.py — Todo CRUD 테스트


class TestCreateTodo:
    def test_create_todo(self, client, auth_headers):
        response = client.post("/todos", json={
            "title": "테스트 할 일",
            "description": "설명",
            "priority": 1,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "테스트 할 일"
        assert data["completed"] is False
        assert data["priority"] == 1

    def test_create_todo_unauthenticated(self, client):
        response = client.post("/todos", json={"title": "테스트"})
        assert response.status_code == 401

    def test_create_todo_invalid(self, client, auth_headers):
        response = client.post("/todos", json={
            "title": "",  # min_length=1 위반
        }, headers=auth_headers)
        assert response.status_code == 422


class TestListTodos:
    def test_list_empty(self, client, auth_headers):
        response = client.get("/todos", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["items"] == []

    def test_list_with_items(self, client, auth_headers):
        client.post("/todos", json={"title": "할 일 1"}, headers=auth_headers)
        client.post("/todos", json={"title": "할 일 2"}, headers=auth_headers)

        response = client.get("/todos", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_list_filter_completed(self, client, auth_headers):
        # 할 일 생성
        res = client.post("/todos", json={"title": "완료할 일"}, headers=auth_headers)
        todo_id = res.json()["id"]

        # 완료 처리
        client.patch(f"/todos/{todo_id}", json={"completed": True}, headers=auth_headers)

        # 미완료만 조회
        response = client.get("/todos?completed=false", headers=auth_headers)
        assert response.json()["total"] == 0

    def test_list_search(self, client, auth_headers):
        client.post("/todos", json={"title": "회의 준비"}, headers=auth_headers)
        client.post("/todos", json={"title": "장보기"}, headers=auth_headers)

        response = client.get("/todos?search=회의", headers=auth_headers)
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["title"] == "회의 준비"


class TestGetTodo:
    def test_get_todo(self, client, auth_headers):
        res = client.post("/todos", json={"title": "조회 테스트"}, headers=auth_headers)
        todo_id = res.json()["id"]

        response = client.get(f"/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "조회 테스트"

    def test_get_todo_not_found(self, client, auth_headers):
        response = client.get("/todos/9999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateTodo:
    def test_update_todo(self, client, auth_headers):
        res = client.post("/todos", json={"title": "수정 전"}, headers=auth_headers)
        todo_id = res.json()["id"]

        response = client.patch(f"/todos/{todo_id}", json={
            "title": "수정 후",
            "completed": True,
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "수정 후"
        assert response.json()["completed"] is True

    def test_partial_update(self, client, auth_headers):
        res = client.post("/todos", json={"title": "원본", "priority": 0}, headers=auth_headers)
        todo_id = res.json()["id"]

        # priority만 수정
        response = client.patch(f"/todos/{todo_id}", json={"priority": 2}, headers=auth_headers)
        assert response.json()["title"] == "원본"  # 변경 안 됨
        assert response.json()["priority"] == 2    # 변경됨


class TestDeleteTodo:
    def test_delete_todo(self, client, auth_headers):
        res = client.post("/todos", json={"title": "삭제 대상"}, headers=auth_headers)
        todo_id = res.json()["id"]

        response = client.delete(f"/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 204

        # 삭제 확인
        response = client.get(f"/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_not_found(self, client, auth_headers):
        response = client.delete("/todos/9999", headers=auth_headers)
        assert response.status_code == 404
