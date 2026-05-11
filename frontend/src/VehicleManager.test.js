import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import VehicleManager from "./VehicleManager";

// Helper: VehicleManager renders 3 dropdowns in order: Make, Model, Port Type.
// Grab labels by position.
const getMakeSelect = () => screen.getAllByRole("combobox")[0];
const getModelSelect = () => screen.getAllByRole("combobox")[1];

// This intercepts all API calls so tests don't need a real backend.
// We dont't use a real backend since we only care about front end logic/behavior.
// Backend has its own tests
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.resetAllMocks();
});

// Helper: makes fetch return a specific JSON response
function mockFetch(data, status = 200) {
  global.fetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  });
}

// Default props passed to VehicleManager
const defaultProps = {
  user: { id: 1, username: "testuser" },
  goToMap: jest.fn(),
};


// Rendering Tests
describe("VehicleManager: Rendering", () => {

  test("shows the page heading and Add Vehicle form", async () => {
    // First fetch: gets /api/auth/me/vehicles , empty list
    mockFetch([]);

    render(<VehicleManager {...defaultProps} />);

    // Page heading
    expect(screen.getByText("My Vehicles")).toBeInTheDocument();

    // Form section title
    expect(screen.getByText("Add a Vehicle")).toBeInTheDocument();

    // Form field labels
    expect(screen.getByText("Make")).toBeInTheDocument();
    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByText("Year")).toBeInTheDocument();
    expect(screen.getByText("Port Type")).toBeInTheDocument();

    // Submit button
    expect(screen.getByRole("button", { name: /add vehicle/i })).toBeInTheDocument();
  });

  test("shows the back to map button", async () => {
    mockFetch([]);

    render(<VehicleManager {...defaultProps} />);

    expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
  });

  test("calls goToMap when back button is clicked", async () => {
    mockFetch([]);
    const goToMap = jest.fn();

    render(<VehicleManager {...defaultProps} goToMap={goToMap} />);

    fireEvent.click(screen.getByRole("button", { name: /map/i }));
    expect(goToMap).toHaveBeenCalledTimes(1);
  });

  test("shows empty state message when no vehicles are saved", async () => {
    mockFetch([]); // empty list

    render(<VehicleManager {...defaultProps} />);

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.getByText(/no vehicles added yet/i)).toBeInTheDocument();
    });
  });

  test("shows '0 vehicles saved' count when list is empty", async () => {
    mockFetch([]);

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument();
    });
  });

  test("renders saved vehicles fetched from the backend", async () => {
    // Simulate backend returning two saved vehicles
    mockFetch([
      { id: 1, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" },
      { id: 2, make: "Nissan", model: "Leaf", year: 2022, port_type: "CHAdeMO" },
    ]);

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/2023 Tesla Model 3/i)).toBeInTheDocument();
      expect(screen.getByText(/2022 Nissan Leaf/i)).toBeInTheDocument();
    });
  });

  test("shows '2 vehicles saved' count when two vehicles are loaded", async () => {
    mockFetch([
      { id: 1, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" },
      { id: 2, make: "Nissan", model: "Leaf", year: 2022, port_type: "CHAdeMO" },
    ]);

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/2 vehicles saved/i)).toBeInTheDocument();
    });
  });

  test("shows error message when loading vehicles fails", async () => {
    // Simulate backend returning a 500 error
    mockFetch({}, 500);

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/could not load vehicles/i)).toBeInTheDocument();
    });
  });

});


// Make / Model Tests
describe("VehicleManager: Make / Model Flow", () => {

  test("model dropdown is disabled before a make is selected", async () => {
    mockFetch([]);

    render(<VehicleManager {...defaultProps} />);

    // The Model dropdown should be disabled when no make is chosen
    await waitFor(() => expect(screen.getAllByRole("combobox").length).toBeGreaterThan(1));
    expect(getModelSelect()).toBeDisabled();
  });

  test("fetches models from NHTSA when a make is selected", async () => {
    // First fetch: load saved vehicles
    mockFetch([]);
    // Second fetch: NHTSA models for a Tesla
    mockFetch({
      Results: [
        { Model_Name: "Model 3" },
        { Model_Name: "Model Y" },
        { Model_Name: "Model S" },
      ],
    });

    render(<VehicleManager {...defaultProps} />);

    // Wait for initial load
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    // Select "Tesla" from the Make dropdown
    fireEvent.change(getMakeSelect(), { target: { value: "Tesla" } });

    // Wait for models to load and appear in the Model dropdown
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "Model 3" })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: "Model Y" })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: "Model S" })).toBeInTheDocument();
    });
  });

  test("model dropdown is enabled after models are fetched", async () => {
    mockFetch([]);
    mockFetch({
      Results: [
        { Model_Name: "Model Y" },
        { Model_Name: "Model 3" },
      ],
    });

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    fireEvent.change(getMakeSelect(), { target: { value: "Tesla" } });

    await waitFor(() => {
      expect(getModelSelect()).not.toBeDisabled();
    });
  });

  test("shows error if model fetch fails", async () => {
    mockFetch([]);         // vehicles
    mockFetch({}, 500);   // NHTSA model fetch fails

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    fireEvent.change(getMakeSelect(), { target: { value: "Ford" } });

    await waitFor(() => {
      expect(screen.getByText(/could not load models for this make/i)).toBeInTheDocument();
    });
  });

});


// Adding A Vehicle Tests
describe("VehicleManager: Adding a Vehicle", () => {

  // Helper: fills out and submits the Add Vehicle form
  async function fillAndSubmitForm({ make = "Tesla", modelName = "Model 3", year = "2023" } = {}) {
    // Select make triggers model fetch
    fireEvent.change(getMakeSelect(), { target: { value: make } });
    // Wait for models to load then pick one
    await waitFor(() => expect(getModelSelect()).not.toBeDisabled());
    fireEvent.change(getModelSelect(), { target: { value: modelName } });
    // Fill in year
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. 2022/i), { target: { value: year } });
    // Submit
    fireEvent.click(screen.getByRole("button", { name: /add vehicle/i }));
  }

  test("shows 'Vehicle added!' success message after a successful post", async () => {
    mockFetch([]);                                    // initial vehicle list
    mockFetch({ Results: [{ Model_Name: "Model 3" }] }); // NHTSA models
    mockFetch(null);                                  // EV specs (model change)
    mockFetch({ id: 10, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" }); // post response
    mockFetch([{ id: 10, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" }]); // refresh list

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    await fillAndSubmitForm();

    await waitFor(() => {
      expect(screen.getByText(/vehicle added!/i)).toBeInTheDocument();
    });
  });

  test("new vehicle appears in the list after successful add", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    mockFetch(null);
    mockFetch({ id: 10, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" });
    mockFetch([{ id: 10, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" }]);

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    await fillAndSubmitForm();

    await waitFor(() => {
      expect(screen.getByText(/2023 Tesla Model 3/i)).toBeInTheDocument();
    });
  });

  test("form resets after a successful add", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    mockFetch(null);
    mockFetch({ id: 10, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" });
    mockFetch([{ id: 10, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" }]);

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    await fillAndSubmitForm();

    // After success, Make dropdown should be reset to default placeholder
    await waitFor(() => {
      expect(getMakeSelect().value).toBe("");
    });
  });

  test("shows error message if the post fails", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    mockFetch(null);
    // post returns 400 with an error detail
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Unknown manufacturer" }),
    });

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    await fillAndSubmitForm();

    await waitFor(() => {
      expect(screen.getByText(/unknown manufacturer/i)).toBeInTheDocument();
    });
  });

  test("submit button is disabled while the post is happening", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    mockFetch(null);

    // Make the post hang so we can check the disabled state
    global.fetch.mockImplementationOnce(() => new Promise(() => { }));

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    fireEvent.change(getMakeSelect(), { target: { value: "Tesla" } });
    await waitFor(() => expect(getModelSelect()).not.toBeDisabled());
    fireEvent.change(getModelSelect(), { target: { value: "Model 3" } });
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. 2022/i), { target: { value: "2023" } });
    fireEvent.click(screen.getByRole("button", { name: /add vehicle/i }));

    // While saving the button text changes and it becomes disabled
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /adding\.\.\./i })).toBeDisabled();
    });
  });

});

//  Deleting A Vehicle Tests
describe("VehicleManager Deleting a Vehicle", () => {

  test("vehicle disappears after clicking Remove", async () => {
    mockFetch([
      { id: 1, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" },
    ]);
    // delete returns 204
    global.fetch.mockResolvedValueOnce({ ok: true, status: 204, json: async () => ({}) });

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => expect(screen.getByText(/2023 Tesla Model 3/i)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /remove/i }));

    await waitFor(() => {
      expect(screen.queryByText(/2023 Tesla Model 3/i)).not.toBeInTheDocument();
    });
  });

  test("vehicle count drops to 0 after removing the only vehicle", async () => {
    mockFetch([
      { id: 1, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" },
    ]);
    global.fetch.mockResolvedValueOnce({ ok: true, status: 204, json: async () => ({}) });

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => expect(screen.getByText(/1 vehicle saved/i)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /remove/i }));

    await waitFor(() => {
      expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument();
    });
  });

  test("only the correct vehicle is removed when there are multiple", async () => {
    mockFetch([
      { id: 1, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" },
      { id: 2, make: "Nissan", model: "Leaf", year: 2022, port_type: "CHAdeMO" },
    ]);
    global.fetch.mockResolvedValueOnce({ ok: true, status: 204, json: async () => ({}) });

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => expect(screen.getByText(/2023 Tesla Model 3/i)).toBeInTheDocument());

    // Click the first remove button
    fireEvent.click(screen.getAllByRole("button", { name: /remove/i })[0]);

    await waitFor(() => {
      expect(screen.queryByText(/2023 Tesla Model 3/i)).not.toBeInTheDocument();
      expect(screen.getByText(/2022 Nissan Leaf/i)).toBeInTheDocument();
    });
  });

  test("shows error message if delete fails", async () => {
    mockFetch([
      { id: 1, make: "Tesla", model: "Model 3", year: 2023, port_type: "CCS (Type 1)" },
    ]);
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) });

    render(<VehicleManager {...defaultProps} />);

    await waitFor(() => expect(screen.getByText(/2023 Tesla Model 3/i)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /remove/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to delete vehicle/i)).toBeInTheDocument();
    });
  });

});

// Autofill Port Type Tests
describe("VehicleManager: Auto fill port type", () => {

  test("shows Auto detected when EV API returns a known port type", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    // EV specs response with a known charge_port
    mockFetch([{ charge_port: "CCS Type 1" }]);

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    fireEvent.change(getMakeSelect(), { target: { value: "Tesla" } });
    await waitFor(() => expect(getModelSelect()).not.toBeDisabled());
    fireEvent.change(getModelSelect(), { target: { value: "Model 3" } });

    await waitFor(() => {
      expect(screen.getByText(/auto-detected/i)).toBeInTheDocument();
    });
  });

  test("does not show Auto detected when EV API returns no port data", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    // EV specs with no charge_port field
    mockFetch([{ charge_port: null }]);

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    fireEvent.change(getMakeSelect(), { target: { value: "Tesla" } });
    await waitFor(() => expect(getModelSelect()).not.toBeDisabled());
    fireEvent.change(getModelSelect(), { target: { value: "Model 3" } });

    await waitFor(() => {
      expect(screen.queryByText(/auto-detected/i)).not.toBeInTheDocument();
    });
  });

  test("Auto detected badge disappears when user manually changes port type", async () => {
    mockFetch([]);
    mockFetch({ Results: [{ Model_Name: "Model 3" }] });
    mockFetch([{ charge_port: "CCS Type 1" }]);

    render(<VehicleManager {...defaultProps} />);
    await waitFor(() => expect(screen.getByText(/0 vehicles saved/i)).toBeInTheDocument());

    fireEvent.change(getMakeSelect(), { target: { value: "Tesla" } });
    await waitFor(() => expect(getModelSelect()).not.toBeDisabled());
    fireEvent.change(getModelSelect(), { target: { value: "Model 3" } });

    // Badge should appear
    await waitFor(() => expect(screen.getByText(/auto-detected/i)).toBeInTheDocument());

    // User manually picks a different port type
    const portSelect = screen.getAllByRole("combobox")[2];
    fireEvent.change(portSelect, { target: { value: "CHAdeMO" } });

    // Badge should disappear
    expect(screen.queryByText(/auto-detected/i)).not.toBeInTheDocument();
  });

});
