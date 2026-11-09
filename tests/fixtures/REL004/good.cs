try
{
    _notifier.SendDispatchSms(job);
}
catch (Exception ex)
{
    _log.LogWarning(ex, "Dispatch SMS failed for job {JobId}", job.Id);
}
