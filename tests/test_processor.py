import unittest
from src.processor import BatchProcessor

class TestBatchProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = BatchProcessor()

    def test_start_processing(self):
        self.processor.start()
        self.assertTrue(self.processor.is_running)

    def test_stop_processing(self):
        self.processor.start()
        self.processor.stop()
        self.assertFalse(self.processor.is_running)

    def test_resume_processing(self):
        self.processor.start()
        self.processor.stop()
        self.processor.resume()
        self.assertTrue(self.processor.is_running)

    def test_process_annotations(self):
        self.processor.start()
        result = self.processor.process_annotations()
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

    def test_handle_interruption(self):
        self.processor.start()
        self.processor.stop()
        state = self.processor.save_state()
        self.assertIsNotNone(state)

if __name__ == '__main__':
    unittest.main()