public async Task<string> GetPart(string id)
{
    using var client = new HttpClient();
    return await client.GetStringAsync($"https://parts/api/{id}");
}
