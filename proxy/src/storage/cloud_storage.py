
    def get_remote_subnets(self):
        """
        Get list of remote subnets to scan
        """
        try:
            response = self._make_request("GET", "/remote-subnets")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Failed to fetch remote subnets: {e}")
            return []
