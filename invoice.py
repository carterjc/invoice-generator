from dataclasses import dataclass, field
from typing import List, Optional
import yaml
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

from time_tracker_summarize import summarize_hours_by_week


@dataclass
class Business:
    name: str
    address: str
    email: str


@dataclass
class Client:
    name: str
    address: str


@dataclass
class InvoiceItem:
    period: str
    description: str
    quantity: float
    rate: float
    amount: float


@dataclass
class Invoice:
    number: str
    date: str
    due_date: str
    notes: str
    subtotal: float = field(init=False)
    total: float = field(init=False)


@dataclass
class Config:
    business: Business
    client: Client
    invoice: Invoice
    items: List[InvoiceItem]
    output: Optional[str] = None


def load_config(config_path: str) -> Config:
    """Load and validate configuration from YAML file"""
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # excluding items is okay
    if "items" not in config_data:
        config_data["items"] = []

    # Validate and parse the YAML data into strict types
    try:
        business = Business(**config_data["business"])
        client = Client(**config_data["client"])
        invoice = Invoice(**config_data["invoice"])
        items = [InvoiceItem(**item) for item in config_data["items"]]

        # Calculate derived values
        invoice.subtotal = sum(item.quantity * item.rate for item in items)
        invoice.total = invoice.subtotal

        # Set default output filename if not provided
        output = config_data.get("output", f"invoice_{invoice.number}.html")

        return Config(
            business=business,
            client=client,
            invoice=invoice,
            items=items,
            output=output,
        )
    except KeyError as e:
        raise ValueError(f"Missing required field in config: {e}")
    except TypeError as e:
        raise ValueError(f"Invalid type in config: {e}")


def render_invoice(config: Config):
    """Render HTML invoice using Jinja2 template"""
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("templates/template.html")

    # Format dates
    config.invoice.date = datetime.strptime(config.invoice.date, "%Y-%m-%d").strftime(
        "%m/%d/%Y"
    )
    config.invoice.due_date = datetime.strptime(
        config.invoice.due_date, "%Y-%m-%d"
    ).strftime("%m/%d/%Y")

    rendered = template.render(
        business=config.business,
        client=config.client,
        invoice=config.invoice,
        items=config.items,
    )

    with open(config.output or "invoice.html", "w") as f:
        f.write(rendered)

    print(f"Invoice generated successfully: {config.output}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate invoice from YAML config")
    parser.add_argument("sheet_name", help="Name of the sheet to process")
    parser.add_argument("filename", help="Path to the Excel file")
    parser.add_argument(
        "--config",
        help="Path to YAML config file (default: config.yaml)",
        default="config.yaml",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        # update items
        summaries = summarize_hours_by_week(args.sheet_name, args.filename)
        config.items = [
            InvoiceItem(
                period=f"{summary["date"].strftime("%m-%d")}-{(summary["date"] + timedelta(7)).strftime("%m-%d")}",
                description=summary["description"],
                quantity=summary["hours"],
                rate=50,
                amount=50 * summary["hours"],
            )
            for summary in summaries
        ]
        # calculate total/subtotal
        total = sum((item.amount for item in config.items))
        config.invoice.subtotal = total
        config.invoice.total = total
        render_invoice(config)
    except ValueError as e:
        print(f"Error loading config: {e}")
