public async Task SyncTechnicianSchedule(int techId)
{
    await _schedule.RefreshAsync(techId);
}
