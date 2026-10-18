import pytest
from job_loader import is_safe_url, extract_job_posting_text

class TestURLSecurityAndSSRF:
    def test_blocks_localhost(self):
        safe, reason = is_safe_url("http://localhost:8080/admin")
        assert not safe
        assert "restricted" in reason.lower() or "internal" in reason.lower()

    def test_blocks_loopback_ipv4(self):
        safe, reason = is_safe_url("http://127.0.0.1:8000/api")
        assert not safe
        assert "restricted" in reason.lower()

    def test_blocks_cloud_metadata_endpoints(self):
        # AWS / GCP / Azure IMDS endpoint
        safe, reason = is_safe_url("http://169.254.169.254/latest/meta-data/")
        assert not safe
        assert "restricted" in reason.lower()

    def test_blocks_private_rfc1918_networks(self):
        # Class A, B, C private IPs
        assert not is_safe_url("http://10.0.0.1/job")[0]
        assert not is_safe_url("http://172.16.0.5/job")[0]
        assert not is_safe_url("http://192.168.1.1/job")[0]

    def test_blocks_non_http_schemes(self):
        assert not is_safe_url("file:///etc/passwd")[0]
        assert not is_safe_url("ftp://server.local/job")[0]
        assert not is_safe_url("gopher://server.local/")[0]

    def test_empty_or_malformed_url(self):
        assert not is_safe_url("")[0]
        assert not is_safe_url("not a url")[0]

    def test_extract_job_posting_text_returns_error_on_blocked_url(self):
        text, err = extract_job_posting_text("http://127.0.0.1/sensitive")
        assert text == ""
        assert err is not None
        assert "Security validation failed" in err
