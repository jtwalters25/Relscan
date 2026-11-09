public class PartsClient
{
    private readonly HttpClient _client;
    public PartsClient(IHttpClientFactory factory) => _client = factory.CreateClient("parts");
    public Task<string> GetPart(string id) => _client.GetStringAsync($"https://parts/api/{id}");
}
