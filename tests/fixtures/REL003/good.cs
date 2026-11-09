// Event handlers are the accepted exception for async void.
private async void OnSubmitClicked(object sender, EventArgs e)
{
    await SubmitAsync();
}
