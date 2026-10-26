from collections.abc import Callable


class AfterCallbackMixin:
    def _init_after_callbacks(self):
        self._pending_after_ids = set()

    def _schedule_after(self, delay_ms: int, callback: Callable[[], None]):
        callback_id = None

        def run():
            self._pending_after_ids.discard(callback_id)
            if self.winfo_exists():
                callback()

        callback_id = self.after(delay_ms, run)
        self._pending_after_ids.add(callback_id)
        return callback_id

    def _cancel_after_callbacks(self):
        for callback_id in tuple(self._pending_after_ids):
            self.after_cancel(callback_id)
        self._pending_after_ids.clear()
