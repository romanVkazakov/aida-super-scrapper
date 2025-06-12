"""
tor_control.py  — lazy NEWNYM helper
────────────────────────────────────
• Подключается к tcp://tor:9051 только по требованию.
• Хранит пул из 3 быстрых exit-нод; каждый renew() берёт следующую.
• Если контрол-порт недоступен — renew() ничего не делает, приложение не падает.
"""
import socket, itertools, time, logging
from stem import Signal
from stem.control import Controller
from stem import SocketError as StemSocketError

CTRL_HOST = "tor"
CTRL_PORT = 9051

_log   = logging.getLogger("tor_control")
_ctrl  = None                 # type: Controller | None
_exits = []                   # fingerprints
_cycle = None                 # itertools.cycle

# ── helpers ───────────────────────────────────────────────────────────────────
def _connect():
    """Single-shot connect; returns Controller or None."""
    global _ctrl
    if _ctrl:
        return _ctrl
    try:
        ip = socket.gethostbyname(CTRL_HOST)
        _ctrl = Controller.from_port(address=ip, port=CTRL_PORT)
        _ctrl.authenticate()
        _log.info("Connected to Tor control on %s:%s", ip, CTRL_PORT)
    except Exception as e:
        _log.warning("Tor control unavailable: %s", e)
        _ctrl = None
    return _ctrl

def _load_exits(n: int = 3):
    """Fetch top-N exit fingerprints by bandwidth."""
    ctl = _connect()
    if not ctl:
        return []
    exits = [r for r in ctl.get_network_statuses()
             if r.exit_policy.is_exiting_allowed()]
    exits.sort(key=lambda r: r.bandwidth or 0, reverse=True)
    return [r.fingerprint for r in exits[:n]]

# ── public API ────────────────────────────────────────────────────────────────
def renew():
    """NEWNYM + переключение на следующий exit из локального пула."""
    global _cycle, _exits
    ctl = _connect()
    if not ctl:
        return                      # контрол-порт недоступен → тихо выходим

    if not _exits:
        _exits = _load_exits()
        _cycle = itertools.cycle(range(len(_exits))) if _exits else None

    exit_fp = None
    if _cycle:
        idx     = next(_cycle)
        exit_fp = _exits[idx]
        try:
            ctl.set_conf("ExitNodes", exit_fp)
            _log.info("Switching to exit %d/%d  %s", idx+1, len(_exits), exit_fp)
        except Exception as e:
            _log.warning("set_conf ExitNodes failed: %s", e)

    try:
        ctl.signal(Signal.NEWNYM)
        time.sleep(1)               # Tor рекомендует ≥ 1 с для постройки цепи
    except StemSocketError as e:
        _log.warning("NEWNYM failed: %s", e)
