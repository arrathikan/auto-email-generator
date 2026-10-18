import pytest
import pandas as pd
from portfolio import Portfolio, sanitize_collection_name

class TestPortfolioMultiUserIsolation:
    def test_sanitize_collection_name(self):
        assert sanitize_collection_name(1) == "user_1_portfolio"
        assert sanitize_collection_name("42") == "user_42_portfolio"
        assert sanitize_collection_name("user@example.com") == "user_user_example_com_portfolio"
        assert sanitize_collection_name(None) == "user_portfolio"

    def test_multi_user_data_isolation(self, tmp_path):
        persist_dir = str(tmp_path / "chroma_test")

        # User A's data
        data_a = pd.DataFrame([
            {"Techstack": "Python, Machine Learning, PyTorch", "Links": "https://github.com/alice/ml-app"},
            {"Techstack": "FastAPI, Docker", "Links": "https://github.com/alice/fastapi-app"}
        ])

        # User B's data
        data_b = pd.DataFrame([
            {"Techstack": "React, TypeScript, CSS", "Links": "https://github.com/bob/react-ui"},
            {"Techstack": "Node.js, Express", "Links": "https://github.com/bob/express-backend"}
        ])

        portfolio_a = Portfolio(data=data_a, user_id=101, persist_directory=persist_dir)
        portfolio_b = Portfolio(data=data_b, user_id=202, persist_directory=persist_dir)

        portfolio_a.load_portfolio(clear_existing=True)
        portfolio_b.load_portfolio(clear_existing=True)

        # 1. User A querying their skills gets User A's links
        links_a = portfolio_a.query_links(["Python", "PyTorch"])
        assert "https://github.com/alice/ml-app" in links_a
        # User A must NEVER see User B's links
        assert "https://github.com/bob/react-ui" not in links_a

        # 2. User B querying their skills gets User B's links
        links_b = portfolio_b.query_links(["React", "TypeScript"])
        assert "https://github.com/bob/react-ui" in links_b
        # User B must NEVER see User A's links
        assert "https://github.com/alice/ml-app" not in links_b

        # 3. Reloading/clearing User A's portfolio must NOT delete or wipe User B's data
        portfolio_a.load_portfolio(clear_existing=True)
        # Verify User B's collection and data still exist intact
        links_b_after = portfolio_b.query_links(["React"])
        assert "https://github.com/bob/react-ui" in links_b_after
