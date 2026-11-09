public async void SyncTechnicianSchedule(int techId)
{
    await _schedule.RefreshAsync(techId);
}
