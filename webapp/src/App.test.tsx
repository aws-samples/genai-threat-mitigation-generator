import { render, screen } from "@testing-library/react";
import App from "./App";
import { vi } from "vitest";

describe("App", () => {
  let mockGetUser = vi.fn();
  mockGetUser.mockReturnValue({firstName: 'John'});

  it("should render successfully", async () => {
    render(<App />);
    expect(screen.getByText('Welcome to React', {exact: false})).toBeInTheDocument();
  });

});
