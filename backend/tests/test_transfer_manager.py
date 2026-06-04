import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import sys

# Mock motor/database if needed
mock_db = MagicMock()
sys.modules["database"] = mock_db
sys.modules["motor"] = MagicMock()
sys.modules["motor.motor_asyncio"] = MagicMock()

from backend.transfer_manager import (
    simulate_tcp_ip, simulate_epidemic, simulate_prophet, 
    generate_baseline_metrics, dtn_transfer_worker
)

class TestTransferLogic(unittest.TestCase):

    def test_tcp_fail_on_drops(self):
        """Requirement 2 & 3: TCP should fail if network drops occur."""
        res = simulate_tcp_ip(total_size_kb=100, drops=1)
        self.assertIn("Failed", res["status"])
        self.assertEqual(res["efficiency"], "Poor")

    def test_dtn_overhead_logic(self):
        """Requirement 3: Verify DTN overhead is lower than Epidemic."""
        total_kb = 100
        epidemic = simulate_epidemic(total_kb)
        dtn = generate_baseline_metrics(0, total_kb)["Neural_DTN"]
        
        epi_val = float(epidemic["overhead"].split()[0])
        dtn_val = float(dtn["overhead"].split()[0])
        
        self.assertLess(dtn_val, epi_val)

    @patch('backend.transfer_manager.transfers.update_one', new_callable=AsyncMock)
    @patch('backend.transfer_manager.log_event', new_callable=AsyncMock)
    @patch('backend.transfer_manager.NETWORK_CONFIG', {"condition": "Real-Time"})
    @patch('backend.transfer_manager.asyncio.sleep', new_callable=AsyncMock) # Speed up test
    def test_dtn_worker_completion(self, mock_sleep, mock_log, mock_update):
        """Verify the background worker logic from start to Delivered status."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(dtn_transfer_worker(
            case_id="TDD_TEST", 
            total_size=1024, # 1KB
            priority="High", 
            real_network_speed=1024*1024, 
            sender="S", 
            receiver="R"
        ))
        
        # Check if Delivered was called
        # The last call to update_one should be the completion call
        final_call = mock_update.call_args_list[-1]
        status = final_call[0][1]['$set']['status']
        self.assertEqual(status, "Delivered ✅")
        
        # Verify baseline comparison was added
        self.assertIn('baseline_comparison', final_call[0][1]['$set'])

if __name__ == '__main__':
    unittest.main()
