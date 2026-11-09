public async Task<string> GetJob(int id)
{
    var job = await _repo.GetJobAsync(id);
    await _repo.SaveAsync(job);
    return await _repo.GetNameAsync(id);
}
