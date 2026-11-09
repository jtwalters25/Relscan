// Sample legacy service in the style of a field-service work order system.
using System.Net.Http;

public class WorkOrderService
{
    public WorkOrder GetWorkOrder(int id)
    {
        return _repo.GetAsync(id).Result;
    }

    public async void NotifyTechnician(int workOrderId)
    {
        var client = new HttpClient();
        await client.PostAsync($"https://notify/api/tech/{workOrderId}", null);
    }

    public void CloseWorkOrder(int id)
    {
        try
        {
            _billing.InvoiceAsync(id).Wait();
        }
        catch { }
    }
}
