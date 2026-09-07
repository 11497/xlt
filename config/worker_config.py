"""异步索引 Worker 与对账服务的运行参数配置。"""

import os


# Worker 每轮任务处理后的轮询间隔，单位：秒。
WORKER_POLL_INTERVAL = float(os.getenv("INDEX_WORKER_POLL_INTERVAL", "2"))

# Worker 连续空转达到阈值后的休眠时长，单位：秒。
WORKER_IDLE_SLEEP = float(os.getenv("INDEX_WORKER_IDLE_SLEEP", "3"))

# 对账服务轮询周期，单位：秒。
RECONCILIATION_POLL_INTERVAL = int(os.getenv("RECONCILE_INTERVAL", "600"))

# 判定 processing 任务卡死的超时时间，单位：分钟。
RECONCILIATION_STUCK_TIMEOUT_MINUTES = int(os.getenv("RECONCILE_STUCK_TIMEOUT", "15"))
