from locust import HttpUser, task, between


class URLShortenerUser(HttpUser):

    wait_time = between(0.1, 0.5)

    @task(9)
    def redirect_url(self):
        self.client.get("/madhav", allow_redirects=False)

    @task(1)
    def create_url(self):
        self.client.post(
            "/urls",
            json={
                "original_url": "https://www.google.com"
            }
        )