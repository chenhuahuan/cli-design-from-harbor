from harborclient import base
from harborclient import utils


class JobManager(base.Manager):
    def list(self, policy_id=None):
        """List filters jobs according to the policy and repository."""
        return self._list("/jobs/replication?policy_id=%s" % policy_id)

    def get_log(self, job_id):
        """Get job logs."""
        return self._get("/jobs/replication/%s/log" % job_id)


@utils.arg(
    'policy_id',
    metavar='<policy_id>',
    help="The policy id.")
def do_job_list(cs, args):
    """List filters jobs according to the policy and repository."""
    jobs = cs.jobs.list(args.policy_id)
    for job in jobs:
        if job['tags']:
            job['name'] += ":" + job['tags']
    fields = ['id', 'repository', 'operation', 'status', 'update_time']
    utils.print_list(jobs, fields, sortby='id')


@utils.arg(
    'job_id',
    metavar='<job_id>',
    help="The job id.")
def do_job_log(cs, args):
    """Get job logs."""
    log = cs.jobs.get_log(args.job_id)
    print(log)