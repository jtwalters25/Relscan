public string GetJob(int id)
{
    var job = _repo.GetJobAsync(id).Result;
    _repo.SaveAsync(job).Wait();
    return _repo.GetNameAsync(id).GetAwaiter().GetResult();
}
