from dataclasses import dataclass

from . import Schema, SchemaCollection


@dataclass
class Facade:
    collection: SchemaCollection

    def campaign(self) -> Schema:
        return self.collection.get_schema_by_name("Campaign.json")

    def campaign_flat(self) -> Schema:
        return self.collection.get_schema_by_name("Campaign_Flat.json")

    def campaign_level_reports(self) -> Schema:
        return self.collection.get_schema_by_name("Row.json")

    def campaign_level_reports_extended_spend_row(self) -> Schema:
        return self.collection.get_schema_by_name("ExtendedSpendRow_campaignId.json")

    def campaign_level_reports_extended_spend_row_flat(self) -> Schema:
        return self.collection.get_schema_by_name(
            "ExtendedSpendRow_campaignId_Flat.json"
        )

    def impression_share_reports(self) -> Schema:
        return self.collection.get_schema_by_name("ImpressionShareDaily.json")
