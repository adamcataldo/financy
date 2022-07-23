from pathlib import Path
import logging
import sys

if __name__ == '__main__':
    parent_dir = str(Path(sys.path[0]).parent.absolute())
    sys.path.extend([parent_dir])
    logging.getLogger().setLevel(logging.INFO)
    import financy.report_generator as rg
    rg.sp_500_report()