import re
import asyncio
import random
from typing import Union
from datetime import datetime

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.constants import *
from sc2.data import Race, Difficulty, ActionResult
from sc2.main import run_game
from sc2.player import Bot, Computer, Human
from sc2.unit import Unit
from sc2.position import Point2, Point3
from sc2.units import Units

from swarmbrain import *


class SwarmBrain(BotAI):
    def __init__(self, command_first, early_values, mid_values, late_values, drone_attack, counterattack):
        super().__init__()
        # print("early_values", early_values)
        # print("mid_values", mid_values)
        # print("late_values", late_values)
        self.early_zergling_num, self.early_baneling_num, self.early_roach_num, self.early_ravager_num, self.early_hydralisk_num, self.early_infestor_num, self.early_swarm_host_num, self.early_mutalisk_num, self.early_corruptor_num, self.early_viper_num, self.early_ultralisk_num, self.early_brood_lord_num = early_values
        self.mid_zergling_num, self.mid_baneling_num, self.mid_roach_num, self.mid_ravager_num, self.mid_hydralisk_num, self.mid_infestor_num, self.mid_swarm_host_num, self.mid_mutalisk_num, self.mid_corruptor_num, self.mid_viper_num, self.mid_ultralisk_num, self.mid_brood_lord_num = mid_values
        self.late_zergling_num, self.late_baneling_num, self.late_roach_num, self.late_ravager_num, self.late_hydralisk_num, self.late_infestor_num, self.late_swarm_host_num, self.late_mutalisk_num, self.late_corruptor_num, self.late_viper_num, self.late_ultralisk_num, self.late_brood_lord_num = late_values

        # print("self.early_hydralisk_num", self.early_hydralisk_num)
        # print("self.mid_hydralisk_num", self.mid_hydralisk_num)
        # print("self.late_hydralisk_num", self.late_hydralisk_num)

        self.start_location_label = None
        self.parsed_commands = []

        self.command_list = command_first
        self.building_tasks = []
        self.attack_tasks = []

        self.mineral_location_labels = {
            (29.5, 65.5): "A1",
            (35.5, 34.5): "A2",
            (56.5, 65.5): "A3",
            (63.5, 26.5): "A4",
            (80.5, 66.5): "A5",
            (98.5, 26.5): "A6",
            (129.5, 28.5): "A7",
            (33.5, 105.5): "A8",
            (154.5, 114.5): "B1",
            (148.5, 145.5): "B2",
            (127.5, 114.5): "B3",
            (120.5, 153.5): "B4",
            (103.5, 113.5): "B5",
            (85.5, 153.5): "B6",
            (54.5, 151.5): "B7",
            (150.5, 74.5): "B8"
        }
        self.mineral_location_labels_reverse = {
            "A1": (29.5, 65.5),
            "A2": (35.5, 34.5),
            "A3": (56.5, 65.5),
            "A4": (63.5, 26.5),
            "A5": (80.5, 66.5),
            "A6": (98.5, 26.5),
            "A7": (129.5, 28.5),
            "A8": (33.5, 105.5),
            "B1": (154.5, 114.5),
            "B2": (148.5, 145.5),
            "B3": (127.5, 114.5),
            "B4": (120.5, 153.5),
            "B5": (103.5, 113.5),
            "B6": (85.5, 153.5),
            "B7": (54.5, 151.5),
            "B8": (150.5, 74.5)
        }

        self.existing_hatchery_locations = []

        self.worker_aggressive = drone_attack
        self.counterattack = counterattack

        self.hatchery_queen_pairs = {}
        self.waiting_for_hatchery = True
        self.is_attack_command_issued = False

        self.previous_enemy_units = {}
        self.previous_enemy_units_attack = {}
        self.previous_enemy_damage = 0
        self.previous_enemy_buildings = {}
        self.previous_commands = []

        self.base_being_attacked = False
        self.defence = False

        self.spread_distance = 13

        self.game_stage = 0

        self.attack_wave = 0

        self.fight_back = False
        self.queen_spread_progress = {}

    async def on_start(self):
        #     # self.client.game_step = 2
        #     # await self.client.debug_show_map()
        start_location_key = tuple(self.start_location)
        # print("start_location_key ", start_location_key)
        self.start_location_label = self.mineral_location_labels.get(start_location_key)

        if self.start_location_label:
            print(f"Our starting location is at {self.start_location_label}")
        else:
            print("Could not determine the start location label.")

        self.command_list = self.filter_commands(self.command_list,
                                                 ['Queen', 'Gather minerals', 'Extractor', 'Mineral', 'Overlord',
                                                  'Move', 'Zergling', 'Creep'])

        if self.start_location_label == "A1":
            Overmind_commands = self.command_list

        new_command_list = []
        if self.start_location_label == "B1":
            for command in self.command_list:
                def replace(match):
                    char, num = match.group(1), match.group(2)
                    return 'B' + num if char == 'A' else 'A' + num

                command = re.sub(r'(A|B)(\d+)', replace, command)
                new_command_list.append(command)

            Overmind_commands = new_command_list

        pattern = re.compile(r'\(([^)]+)\)')

        for command in Overmind_commands:
            parts = pattern.findall(command)
            self.parsed_commands.append(parts)
        # print("self.parsed_commands:", self.parsed_commands)

    def get_units_distribution(self):
        distribution = {}
        for mineral_position, location_label in self.mineral_location_labels.items():
            units_near_townhall = self.units.closer_than(20, mineral_position)

            larvas_near_townhall = units_near_townhall.of_type({UnitTypeId.LARVA})
            drones_near_townhall = units_near_townhall.of_type({UnitTypeId.DRONE})
            overlords_near_townhall = units_near_townhall.of_type({UnitTypeId.OVERLORD})
            queens_near_townhall = units_near_townhall.of_type({UnitTypeId.QUEEN})
            zerglings_near_townhall = units_near_townhall.of_type({UnitTypeId.ZERGLING})
            overseers_near_townhall = units_near_townhall.of_type({UnitTypeId.OVERSEER})
            roaches_near_townhall = units_near_townhall.of_type({UnitTypeId.ROACH})
            ravagers_near_townhall = units_near_townhall.of_type({UnitTypeId.RAVAGER})
            banelings_near_townhall = units_near_townhall.of_type({UnitTypeId.BANELING})
            hydralisks_near_townhall = units_near_townhall.of_type({UnitTypeId.HYDRALISK})
            infestors_near_townhall = units_near_townhall.of_type({UnitTypeId.INFESTOR})
            swarmhosts_near_townhall = units_near_townhall.of_type({UnitTypeId.SWARMHOSTMP})
            mutalisks_near_townhall = units_near_townhall.of_type({UnitTypeId.MUTALISK})
            corruptors_near_townhall = units_near_townhall.of_type({UnitTypeId.CORRUPTOR})
            vipers_near_townhall = units_near_townhall.of_type({UnitTypeId.VIPER})
            ultralisks_near_townhall = units_near_townhall.of_type({UnitTypeId.ULTRALISK})
            broodlord_near_townhall = units_near_townhall.of_type({UnitTypeId.BROODLORD})

            # Now collect the summary for this point
            unit_summary = f""
            if larvas_near_townhall.amount > 0:
                unit_summary += f"{larvas_near_townhall.amount} Larvas are idling"
            if drones_near_townhall.amount > 0:
                unit_summary += f", {drones_near_townhall.amount} Drones are gathering mineral and gas in Hatchery"
            if overlords_near_townhall.amount > 0:
                unit_summary += f", {overlords_near_townhall.amount} Overlords are idling"
            if queens_near_townhall.amount > 0:
                unit_summary += f", {queens_near_townhall.amount} Queens are idling"
            if zerglings_near_townhall.amount > 0:
                unit_summary += f", {zerglings_near_townhall.amount} Zerglings are idling"
            if overseers_near_townhall.amount > 0:
                unit_summary += f", {overseers_near_townhall.amount} Overseers are idling"
            if roaches_near_townhall.amount > 0:
                unit_summary += f", {roaches_near_townhall.amount} Roaches are idling"
            if ravagers_near_townhall.amount > 0:
                unit_summary += f", {ravagers_near_townhall.amount} Ravagers are idling"
            if banelings_near_townhall.amount > 0:
                unit_summary += f", {banelings_near_townhall.amount} Banelings are idling"
            if hydralisks_near_townhall.amount > 0:
                unit_summary += f", {hydralisks_near_townhall.amount} Hydralisks are idling"
            if infestors_near_townhall.amount > 0:
                unit_summary += f", {infestors_near_townhall.amount} Infestors are idling"
            if swarmhosts_near_townhall.amount > 0:
                unit_summary += f", {swarmhosts_near_townhall.amount} Swarm Hosts are idling"
            if mutalisks_near_townhall.amount > 0:
                unit_summary += f", {mutalisks_near_townhall.amount} Mutalisks are idling"
            if corruptors_near_townhall.amount > 0:
                unit_summary += f", {corruptors_near_townhall.amount} Corruptors are idling"
            if vipers_near_townhall.amount > 0:
                unit_summary += f", {vipers_near_townhall.amount} Vipers are idling"
            if ultralisks_near_townhall.amount > 0:
                unit_summary += f", {ultralisks_near_townhall.amount} Ultralisks are idling"
            if broodlord_near_townhall.amount > 0:
                unit_summary += f", {broodlord_near_townhall.amount} Brood Lords are idling"

            if unit_summary == "":
                continue
            # Assign the summary to the distribution dict
            distribution[location_label] = unit_summary

        return distribution

    def get_units_all(self):
        drones = self.units(UnitTypeId.DRONE).amount
        overlords = self.units(UnitTypeId.OVERLORD).amount
        queens = self.units(UnitTypeId.QUEEN).amount
        zerglings = self.units(UnitTypeId.ZERGLING).amount
        overseers = self.units(UnitTypeId.OVERSEER).amount
        roaches = self.units(UnitTypeId.ROACH).amount
        ravagers = self.units(UnitTypeId.RAVAGER).amount
        banelings = self.units(UnitTypeId.BANELING).amount
        hydralisks = self.units(UnitTypeId.HYDRALISK).amount
        infestors = self.units(UnitTypeId.INFESTOR).amount
        swarmhosts = self.units(UnitTypeId.SWARMHOSTMP).amount
        mutalisks = self.units(UnitTypeId.MUTALISK).amount
        corruptors = self.units(UnitTypeId.CORRUPTOR).amount
        vipers = self.units(UnitTypeId.VIPER).amount
        ultralisks = self.units(UnitTypeId.ULTRALISK).amount
        broodlords = self.units(UnitTypeId.BROODLORD).amount

        summary = f""
        if drones > 0:
            summary += f"{drones} Drones"
        if overlords > 0:
            if summary:
                summary += f", {overlords} Overlords"
            else:
                summary += f"{overlords} Overlords"
        if queens > 0:
            if summary:
                summary += f", {queens} Queens"
            else:
                summary += f"{queens} Queens"
        if zerglings > 0:
            if summary:
                summary += f", {zerglings} Zerglings"
            else:
                summary += f"{zerglings} Zerglings"
        if overseers > 0:
            if summary:
                summary += f", {overseers} Overseers"
            else:
                summary += f"{overseers} Overseers"
        if roaches > 0:
            if summary:
                summary += f", {roaches} Roaches"
            else:
                summary += f"{roaches} Roaches"
        if ravagers > 0:
            if summary:
                summary += f", {ravagers} Ravagers"
            else:
                summary += f"{ravagers} Ravagers"
        if banelings > 0:
            if summary:
                summary += f", {banelings} Banelings"
            else:
                summary += f"{banelings} Banelings"
        if hydralisks > 0:
            if summary:
                summary += f", {hydralisks} Hydralisks"
            else:
                summary += f"{hydralisks} Hydralisks"
        if infestors > 0:
            if summary:
                summary += f", {infestors} Infestors"
            else:
                summary += f"{infestors} Infestors"
        if swarmhosts > 0:
            if summary:
                summary += f", {swarmhosts} Swarm Hosts"
            else:
                summary += f"{swarmhosts} Swarm Hosts"
        if mutalisks > 0:
            if summary:
                summary += f", {mutalisks} Mutalisks"
            else:
                summary += f"{mutalisks} Mutalisks"
        if corruptors > 0:
            if summary:
                summary += f", {corruptors} Corruptors"
            else:
                summary += f"{corruptors} Corruptors"
        if vipers > 0:
            if summary:
                summary += f", {vipers} Vipers"
            else:
                summary += f"{vipers} Vipers"
        if ultralisks > 0:
            if summary:
                summary += f", {ultralisks} Ultralisks"
            else:
                summary += f"{ultralisks} Ultralisks"
        if broodlords > 0:
            if summary:
                summary += f", {broodlords} Brood Lords"
            else:
                summary += f"{broodlords} Brood Lords"

        return summary

    def get_units_all_attack(self):
        zerglings = self.units(UnitTypeId.ZERGLING).amount
        roaches = self.units(UnitTypeId.ROACH).amount
        ravagers = self.units(UnitTypeId.RAVAGER).amount
        banelings = self.units(UnitTypeId.BANELING).amount
        hydralisks = self.units(UnitTypeId.HYDRALISK).amount
        infestors = self.units(UnitTypeId.INFESTOR).amount
        swarmhosts = self.units(UnitTypeId.SWARMHOSTMP).amount
        mutalisks = self.units(UnitTypeId.MUTALISK).amount
        corruptors = self.units(UnitTypeId.CORRUPTOR).amount
        vipers = self.units(UnitTypeId.VIPER).amount
        ultralisks = self.units(UnitTypeId.ULTRALISK).amount
        broodlords = self.units(UnitTypeId.BROODLORD).amount

        army_damage = zerglings * 5 + roaches * 16 + ravagers * 16 + banelings * 16 + hydralisks * 12 + mutalisks * 9 + corruptors * 14 + ultralisks * 35 + broodlords * 20

        summary = f""
        if zerglings > 0:
            summary += f"{zerglings} Zerglings"
        if roaches > 0:
            if summary:
                summary += f", {roaches} Roaches"
            else:
                summary += f"{roaches} Roaches"
        if ravagers > 0:
            if summary:
                summary += f", {ravagers} Ravagers"
            else:
                summary += f"{ravagers} Ravagers"
        if banelings > 0:
            if summary:
                summary += f", {banelings} Banelings"
            else:
                summary += f"{banelings} Banelings"
        if hydralisks > 0:
            if summary:
                summary += f", {hydralisks} Hydralisks"
            else:
                summary += f"{hydralisks} Hydralisks"
        if infestors > 0:
            if summary:
                summary += f", {infestors} Infestors"
            else:
                summary += f"{infestors} Infestors"
        if swarmhosts > 0:
            if summary:
                summary += f", {swarmhosts} Swarm Hosts"
            else:
                summary += f"{swarmhosts} Swarm Hosts"
        if mutalisks > 0:
            if summary:
                summary += f", {mutalisks} Mutalisks"
            else:
                summary += f"{mutalisks} Mutalisks"
        if corruptors > 0:
            if summary:
                summary += f", {corruptors} Corruptors"
            else:
                summary += f"{corruptors} Corruptors"
        if vipers > 0:
            if summary:
                summary += f", {vipers} Vipers"
            else:
                summary += f"{vipers} Vipers"
        if ultralisks > 0:
            if summary:
                summary += f", {ultralisks} Ultralisks"
            else:
                summary += f"{ultralisks} Ultralisks"
        if broodlords > 0:
            if summary:
                summary += f", {broodlords} Brood Lords"
            else:
                summary += f"{broodlords} Brood Lords"

        return summary, army_damage

    def get_buildings_distribution(self):
        distribution = {}
        for townhall in self.townhalls.ready:
            townhall_location_label = self.mineral_location_labels.get(townhall.position)

            buildings_near_townhall = self.structures.closer_than(20, townhall.position)

            extractor_near_townhall = buildings_near_townhall.of_type({UnitTypeId.EXTRACTOR})
            spawningpool_near_townhall = buildings_near_townhall.of_type({UnitTypeId.SPAWNINGPOOL})
            evolutionchamber_near_townhall = buildings_near_townhall.of_type({UnitTypeId.EVOLUTIONCHAMBER})
            roachwarren_near_townhall = buildings_near_townhall.of_type({UnitTypeId.ROACHWARREN})
            banelingnest_near_townhall = buildings_near_townhall.of_type({UnitTypeId.BANELINGNEST})
            spinecrawler_near_townhall = buildings_near_townhall.of_type({UnitTypeId.SPINECRAWLER})
            sporecrawler_near_townhall = buildings_near_townhall.of_type({UnitTypeId.SPORECRAWLER})
            hydraliskden_near_townhall = buildings_near_townhall.of_type({UnitTypeId.HYDRALISKDEN})
            infestationpit_near_townhall = buildings_near_townhall.of_type({UnitTypeId.INFESTATIONPIT})
            spire_near_townhall = buildings_near_townhall.of_type({UnitTypeId.SPIRE})
            nydusnetwork_near_townhall = buildings_near_townhall.of_type({UnitTypeId.NYDUSNETWORK})
            ultraliskcavern_near_townhall = buildings_near_townhall.of_type({UnitTypeId.ULTRALISKCAVERN})
            greaterspire_near_townhall = buildings_near_townhall.of_type({UnitTypeId.GREATERSPIRE})

            unit_summary = f"1 {townhall.name.lower()}"
            if extractor_near_townhall.amount > 0:
                unit_summary += f", {extractor_near_townhall.amount} Extractor"
            if spawningpool_near_townhall.amount > 0:
                unit_summary += f", {spawningpool_near_townhall.amount} Spawning Pool"
            if evolutionchamber_near_townhall.amount > 0:
                unit_summary += f", {evolutionchamber_near_townhall.amount} Evolution Chamber"
            if roachwarren_near_townhall.amount > 0:
                unit_summary += f", {roachwarren_near_townhall.amount} Roach Warren"
            if banelingnest_near_townhall.amount > 0:
                unit_summary += f", {banelingnest_near_townhall.amount} Baneling Nest"
            if spinecrawler_near_townhall.amount > 0:
                unit_summary += f", {spinecrawler_near_townhall.amount} Spine Crawler"
            if sporecrawler_near_townhall.amount > 0:
                unit_summary += f", {sporecrawler_near_townhall.amount} Spore Crawler"
            if hydraliskden_near_townhall.amount > 0:
                unit_summary += f", {hydraliskden_near_townhall.amount} Hydralisk Den"
            if infestationpit_near_townhall.amount > 0:
                unit_summary += f", {infestationpit_near_townhall.amount} Infestation Pit"
            if spire_near_townhall.amount > 0:
                unit_summary += f", {spire_near_townhall.amount} Spire"
            if nydusnetwork_near_townhall.amount > 0:
                unit_summary += f", {nydusnetwork_near_townhall.amount} Nydus Network"
            if ultraliskcavern_near_townhall.amount > 0:
                unit_summary += f", {ultraliskcavern_near_townhall.amount} Ultralisk Cavern"
            if greaterspire_near_townhall.amount > 0:
                unit_summary += f", {greaterspire_near_townhall.amount} Greater Spire"
            distribution[townhall_location_label] = unit_summary

        return distribution

    def get_buildings_all(self):
        hatchery = self.structures(UnitTypeId.HATCHERY).amount
        lair = self.structures(UnitTypeId.LAIR).amount
        hive = self.structures(UnitTypeId.HIVE).amount
        extractor = self.structures(UnitTypeId.EXTRACTOR).amount
        spawningpool = self.structures(UnitTypeId.SPAWNINGPOOL).amount
        evolutionchamber = self.structures(UnitTypeId.EVOLUTIONCHAMBER).amount
        roachwarren = self.structures(UnitTypeId.ROACHWARREN).amount
        banelingnest = self.structures(UnitTypeId.BANELINGNEST).amount
        spinecrawler = self.structures(UnitTypeId.SPINECRAWLER).amount
        sporecrawler = self.structures(UnitTypeId.SPORECRAWLER).amount
        hydraliskden = self.structures(UnitTypeId.HYDRALISKDEN).amount
        infestationpit = self.structures(UnitTypeId.INFESTATIONPIT).amount
        spire = self.structures(UnitTypeId.SPIRE).amount
        nydusnetwork = self.structures(UnitTypeId.NYDUSNETWORK).amount
        ultraliskcavern = self.structures(UnitTypeId.ULTRALISKCAVERN).amount
        greaterspire = self.structures(UnitTypeId.GREATERSPIRE).amount

        summary = f""
        if hatchery > 0:
            summary += f"{hatchery} Hatchery"
        if lair > 0:
            summary += f", {lair} Lair"
        if hive > 0:
            summary += f", {hive} Hive"
        if extractor > 0:
            summary += f", {extractor} Extractor"
        if spawningpool > 0:
            summary += f", {spawningpool} Spawningpool"
        if evolutionchamber > 0:
            summary += f", {evolutionchamber} Evolution Chamber"
        if roachwarren > 0:
            summary += f", {roachwarren} Roach Warren"
        if banelingnest > 0:
            summary += f", {banelingnest} Baneling Nest"
        if spinecrawler > 0:
            summary += f", {spinecrawler} Spine Crawler"
        if sporecrawler > 0:
            summary += f", {sporecrawler} Spore Crawler"
        if hydraliskden > 0:
            summary += f", {hydraliskden} Hydralisk Den"
        if infestationpit > 0:
            summary += f", {infestationpit} Infestation Pit"
        if spire > 0:
            summary += f", {spire} Spire"
        if nydusnetwork > 0:
            summary += f", {nydusnetwork} Nydus Network"
        if ultraliskcavern > 0:
            summary += f", {ultraliskcavern} Ultralisk Cavern"
        if greaterspire > 0:
            summary += f", {greaterspire} Greater Spire"

        return summary

    def get_tech(self):
        tech_info = []
        for upgrade in self.state.upgrades:
            upgrade_name = upgrade.name
            tech_info.append(upgrade_name)
        return tech_info

    def get_enemy_units(self):
        if len(self.enemy_units) == 0:
            return {}
        distribution = {}

        for mineral_position, location_label in self.mineral_location_labels.items():
            units_near_mineral = self.enemy_units.closer_than(25, mineral_position)

            scv_near_mineral = units_near_mineral.of_type({UnitTypeId.SCV})
            marine_near_mineral = units_near_mineral.of_type({UnitTypeId.MARINE})
            reaper_near_mineral = units_near_mineral.of_type({UnitTypeId.REAPER})
            marauder_near_mineral = units_near_mineral.of_type({UnitTypeId.MARAUDER})
            ghost_near_mineral = units_near_mineral.of_type({UnitTypeId.GHOST})
            hellion_near_mineral = units_near_mineral.of_type({UnitTypeId.HELLION})
            widowmine_near_mineral = units_near_mineral.of_type({UnitTypeId.WIDOWMINE})
            cyclone_near_mineral = units_near_mineral.of_type({UnitTypeId.CYCLONE})
            siegetank_near_mineral = units_near_mineral.of_type({UnitTypeId.SIEGETANK})
            hellbat_near_mineral = units_near_mineral.of_type({UnitTypeId.HELLBATACGLUESCREENDUMMY})
            thor_near_mineral = units_near_mineral.of_type({UnitTypeId.THOR})
            viking_near_mineral = units_near_mineral.of_type({UnitTypeId.VIKING})
            medivac_near_mineral = units_near_mineral.of_type({UnitTypeId.MEDIVAC})
            liberator_near_mineral = units_near_mineral.of_type({UnitTypeId.LIBERATOR})
            raven_near_mineral = units_near_mineral.of_type({UnitTypeId.RAVEN})
            banshee_near_mineral = units_near_mineral.of_type({UnitTypeId.BANSHEE})
            battlecruiser_near_mineral = units_near_mineral.of_type({UnitTypeId.BATTLECRUISER})

            unit_summary = f""
            if scv_near_mineral.amount > 0:
                unit_summary += f"{scv_near_mineral.amount} SCVs"
            if marine_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {marine_near_mineral.amount} Marines"
                else:
                    unit_summary += f"{marine_near_mineral.amount} Marines"
            if reaper_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {reaper_near_mineral.amount} Reapers"
                else:
                    unit_summary += f"{reaper_near_mineral.amount} Reapers"
            if marauder_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {marauder_near_mineral.amount} Marauders"
                else:
                    unit_summary += f"{marauder_near_mineral.amount} Marauders"
            if ghost_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {ghost_near_mineral.amount} Ghosts"
                else:
                    unit_summary += f"{ghost_near_mineral.amount} Ghosts"
            if hellion_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {hellion_near_mineral.amount} Hellions"
                else:
                    unit_summary += f"{hellion_near_mineral.amount} Hellions"
            if widowmine_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {widowmine_near_mineral.amount} Widow Mines"
                else:
                    unit_summary += f"{widowmine_near_mineral.amount} Widow Mines"
            if cyclone_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {cyclone_near_mineral.amount} Cyclones"
                else:
                    unit_summary += f"{cyclone_near_mineral.amount} Cyclones"
            if siegetank_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {siegetank_near_mineral.amount} Siege Tanks"
                else:
                    unit_summary += f"{siegetank_near_mineral.amount} Siege Tanks"
            if hellbat_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {hellbat_near_mineral.amount} Hellbats"
                else:
                    unit_summary += f"{hellbat_near_mineral.amount} Hellbats"
            if thor_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {thor_near_mineral.amount} Thors"
                else:
                    unit_summary += f"{thor_near_mineral.amount} Thors"
            if viking_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {viking_near_mineral.amount} Vikings"
                else:
                    unit_summary += f"{viking_near_mineral.amount} Vikings"
            if medivac_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {medivac_near_mineral.amount} Medivacs"
                else:
                    unit_summary += f"{medivac_near_mineral.amount} Medivacs"
            if liberator_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {liberator_near_mineral.amount} Liberators"
                else:
                    unit_summary += f"{liberator_near_mineral.amount} Liberators"
            if raven_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {raven_near_mineral.amount} Ravens"
                else:
                    unit_summary += f"{raven_near_mineral.amount} Ravens"
            if banshee_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {banshee_near_mineral.amount} Banshees"
                else:
                    unit_summary += f"{banshee_near_mineral.amount} Banshees"
            if battlecruiser_near_mineral.amount > 0:
                if unit_summary:
                    unit_summary += f", {battlecruiser_near_mineral.amount} Battle Cruisers"
                else:
                    unit_summary += f"{battlecruiser_near_mineral.amount} Battle Cruisers"

            if unit_summary == "":
                continue

            distribution[location_label] = unit_summary

        return distribution

    def get_enemy_units_all(self):
        marines = self.enemy_units(UnitTypeId.MARINE).amount
        reapers = self.enemy_units(UnitTypeId.REAPER).amount
        marauders = self.enemy_units(UnitTypeId.MARAUDER).amount
        ghosts = self.enemy_units(UnitTypeId.GHOST).amount
        hellions = self.enemy_units(UnitTypeId.HELLION).amount
        widowmines = self.enemy_units(UnitTypeId.WIDOWMINE).amount
        cyclones = self.enemy_units(UnitTypeId.CYCLONE).amount
        siegetanks = self.enemy_units(UnitTypeId.SIEGETANK).amount
        hellbats = self.enemy_units(UnitTypeId.HELLBATACGLUESCREENDUMMY).amount
        thors = self.enemy_units(UnitTypeId.THOR).amount
        vikings = self.enemy_units(UnitTypeId.VIKING).amount
        medivacs = self.enemy_units(UnitTypeId.MEDIVAC).amount
        liberators = self.enemy_units(UnitTypeId.LIBERATOR).amount
        ravens = self.enemy_units(UnitTypeId.RAVEN).amount
        banshees = self.enemy_units(UnitTypeId.BANSHEE).amount
        battlecruisers = self.enemy_units(UnitTypeId.BATTLECRUISER).amount

        enemy_damage = marines * 6 + reapers * 4 + marauders * 10 + ghosts * 10 + hellions * 8 + widowmines * 125 + cyclones * 11 + siegetanks * 40 + hellbats * 18 + thors * 30 + vikings * 12 + liberators * 5 + banshees * 12 + battlecruisers * 8

        summary = f""
        if marines > 0:
            summary += f"{marines} Marines"
        if reapers > 0:
            if summary:
                summary += f", {reapers} Reapers"
            else:
                summary += f", {reapers} Reapers"
        if marauders > 0:
            if summary:
                summary += f", {marauders} Marauders"
            else:
                summary += f"{marauders} Marauders"
        if ghosts > 0:
            if summary:
                summary += f", {ghosts} Ghosts"
            else:
                summary += f"{ghosts} Ghosts"
        if hellions > 0:
            if summary:
                summary += f", {hellions} Hellions"
            else:
                summary += f"{hellions} Hellions"
        if widowmines > 0:
            if summary:
                summary += f", {widowmines} Widow Mines"
            else:
                summary += f", {widowmines} Widow Mines"
        if cyclones > 0:
            if summary:
                summary += f", {cyclones} Cyclones"
            else:
                summary += f"{cyclones} Cyclones"
        if siegetanks > 0:
            if summary:
                summary += f", {siegetanks} Siege Tanks"
            else:
                summary += f"{siegetanks} Siege Tanks"
        if hellbats > 0:
            if summary:
                summary += f", {hellbats} Hellbats"
            else:
                summary += f"{hellbats} Hellbats"
        if thors > 0:
            if summary:
                summary += f", {thors} Thors"
            else:
                summary += f"{thors} Thors"
        if vikings > 0:
            if summary:
                summary += f", {vikings} Vikings"
            else:
                summary += f"{vikings} Vikings"
        if medivacs > 0:
            if summary:
                summary += f", {medivacs} Medivacs"
            else:
                summary += f"{medivacs} Medivacs"
        if liberators > 0:
            if summary:
                summary += f", {liberators} Liberators"
            else:
                summary += f"{liberators} Liberators"
        if ravens > 0:
            if summary:
                summary += f", {ravens} Ravens"
            else:
                summary += f"{ravens} Ravens"
        if banshees > 0:
            if summary:
                summary += f", {banshees} Banshees"
            else:
                summary += f"{banshees} Banshees"
        if battlecruisers > 0:
            if summary:
                summary += f", {battlecruisers} Battlecruisers"
            else:
                summary += f"{battlecruisers} Battlecruisers"

        return summary, enemy_damage

    def get_enemy_buildings(self):
        if len(self.enemy_structures) == 0:
            return {}
        distribution = {}

        for mineral_position, location_label in self.mineral_location_labels.items():
            units_near_mineral = self.enemy_structures.closer_than(25, mineral_position)

            commandcenter_near_townhall = units_near_mineral.of_type({UnitTypeId.COMMANDCENTER})
            refinery_near_townhall = units_near_mineral.of_type({UnitTypeId.REFINERY})
            supplydepot_near_townhall = units_near_mineral.of_type({UnitTypeId.SUPPLYDEPOT})
            engineeringbay_near_townhall = units_near_mineral.of_type({UnitTypeId.ENGINEERINGBAY})
            missileturret_near_townhall = units_near_mineral.of_type({UnitTypeId.MISSILETURRET})
            sensortower_near_townhall = units_near_mineral.of_type({UnitTypeId.SENSORTOWER})
            planetaryfortress_near_townhall = units_near_mineral.of_type({UnitTypeId.PLANETARYFORTRESS})
            barracks_near_townhall = units_near_mineral.of_type({UnitTypeId.BARRACKS})
            bunker_near_townhall = units_near_mineral.of_type({UnitTypeId.BUNKER})
            ghostacademy_near_townhall = units_near_mineral.of_type({UnitTypeId.GHOSTACADEMY})
            factory_near_townhall = units_near_mineral.of_type({UnitTypeId.FACTORY})
            orbitalcommand_near_townhall = units_near_mineral.of_type({UnitTypeId.ORBITALCOMMAND})
            armory_near_townhall = units_near_mineral.of_type({UnitTypeId.ARMORY})
            starport_near_townhall = units_near_mineral.of_type({UnitTypeId.STARPORT})
            fusioncore_near_townhall = units_near_mineral.of_type({UnitTypeId.FUSIONCORE})

            unit_summary = f""
            if commandcenter_near_townhall.amount > 0:
                unit_summary += f"{commandcenter_near_townhall.amount} Command Center"
            if refinery_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {refinery_near_townhall.amount} Refinery"
                else:
                    unit_summary += f"{refinery_near_townhall.amount} Refinery"
            if supplydepot_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {supplydepot_near_townhall.amount} Supply Depot"
                else:
                    unit_summary += f"{supplydepot_near_townhall.amount} Supply Depot"
            if engineeringbay_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {engineeringbay_near_townhall.amount} Engineering Bay"
                else:
                    unit_summary += f"{engineeringbay_near_townhall.amount} Engineering Bay"
            if missileturret_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {missileturret_near_townhall.amount} Missile Turret"
                else:
                    unit_summary += f"{missileturret_near_townhall.amount} Missile Turret"
            if sensortower_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {sensortower_near_townhall.amount} Sensor Tower"
                else:
                    unit_summary += f"{sensortower_near_townhall.amount} Sensor Tower"
            if planetaryfortress_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {planetaryfortress_near_townhall.amount} Planetary Fortress"
                else:
                    unit_summary += f"{planetaryfortress_near_townhall.amount} Planetary Fortress"
            if barracks_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {barracks_near_townhall.amount} Barracks"
                else:
                    unit_summary += f"{barracks_near_townhall.amount} Barracks"
            if bunker_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {bunker_near_townhall.amount} Bunker"
                else:
                    unit_summary += f"{bunker_near_townhall.amount} Bunker"
            if ghostacademy_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {ghostacademy_near_townhall.amount} Ghost Academy"
                else:
                    unit_summary += f"{ghostacademy_near_townhall.amount} Ghost Academy"
            if factory_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {factory_near_townhall.amount} Factory"
                else:
                    unit_summary += f"{factory_near_townhall.amount} Factory"
            if orbitalcommand_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {orbitalcommand_near_townhall.amount} Orbital Command"
                else:
                    unit_summary += f"{orbitalcommand_near_townhall.amount} Orbital Command"
            if armory_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {armory_near_townhall.amount} Armory"
                else:
                    unit_summary += f", {armory_near_townhall.amount} Armory"
            if starport_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {starport_near_townhall.amount} Starport"
                else:
                    unit_summary += f"{starport_near_townhall.amount} Starport"
            if fusioncore_near_townhall.amount > 0:
                if unit_summary:
                    unit_summary += f", {fusioncore_near_townhall.amount} Fusion Core"
                else:
                    unit_summary += f"{fusioncore_near_townhall.amount} Fusion Core"

            if unit_summary == "":
                continue

            distribution[location_label] = unit_summary

        return distribution

    def filter_commands(self, commands, target_objects):
        filtered_commands = [cmd for cmd in commands if not any(obj in cmd for obj in target_objects)]
        return filtered_commands

    def id_game_stage(self):
        if self.supply_cap <= 60:
            return 0  # early
        elif self.supply_cap > 60:
            return 1  # mid
        elif self.supply_cap > 100:
            return 2  # late

    def detect_stage(self, text):
        if 'early' in text and 'mid' not in text:
            return 0
        elif 'early' in text and 'mid' in text:
            return 1
        elif 'late' in text:
            return 2
        return self.id_game_stage()

    async def overmindbrain_iter(self):
        game_time = self.time_formatted

        tmp_current_units = []
        current_units = self.get_units_distribution()
        print("our units:")
        for location, units_summary in current_units.items():
            if self.start_location_label == "B1":
                location = location.replace('B', 'A')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_units.append(f"At point {location}, there are: {units_summary}")

        tmp_current_buildings = []
        current_buildings = self.get_buildings_distribution()
        print("our buildings:")
        for location, units_summary in current_buildings.items():
            if self.start_location_label == "B1":
                location = location.replace('B', 'A')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_buildings.append(f"At point {location}, there are: {units_summary}")

        current_tech = self.get_tech()
        print("our tech:")
        print("current_tech:", current_tech)

        tmp_current_enemy_units = []
        current_enemy_units = self.get_enemy_units()
        if current_enemy_units == "":
            current_enemy_units = self.previous_enemy_units
        self.previous_enemy_units = current_enemy_units

        for location, units_summary in current_enemy_units.items():
            if self.start_location_label == "B1":
                location = location.replace('A', 'B')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_enemy_units.append(f"At point {location}, there are: {units_summary}")

        tmp_current_enemy_buildings = []
        current_enemy_buildings = self.get_enemy_buildings()
        if current_enemy_buildings == "":
            current_enemy_buildings = self.previous_enemy_buildings
        self.previous_enemy_buildings = current_enemy_buildings
        print("enemy buildings:")
        for location, units_summary in current_enemy_buildings.items():
            if self.start_location_label == "B1":
                location = location.replace('A', 'B')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_enemy_buildings.append(f"At point {location}, there are: {units_summary}")

        output = await overmind_brain_iter(game_time, tmp_current_units, tmp_current_buildings, current_tech,
                                           tmp_current_enemy_units,
                                           tmp_current_enemy_buildings, self.previous_commands)
        print(output)

        # self.game_stage = self.detect_stage(output)

        matches = re.findall(r'\(.*?\)->\(.*?\)->\(.*?\)', output)

        temp_commands = []
        for match in matches:
            temp_commands.append(match)

        self.previous_commands = temp_commands

        temp_commands = self.filter_commands(temp_commands,
                                             ['Queen', 'Gather minerals', 'Extractor', 'Mineral', 'Overlord', 'Move',
                                              'Zergling', 'Creep'])

        temp_commands_reverse = []
        if self.start_location_label == "A1":
            temp_commands_reverse = temp_commands
        elif self.start_location_label == "B1":
            for command in temp_commands:
                def replace(match):
                    char, num = match.group(1), match.group(2)
                    return 'B' + num if char == 'A' else 'A' + num

                command = re.sub(r'(A|B)(\d+)', replace, command)
                temp_commands_reverse.append(command)

        pattern = re.compile(r'\(([^)]+)\)')

        for command in temp_commands_reverse:
            parts = pattern.findall(command)
            self.parsed_commands.append(parts)

        print("self.parsed_commands:", self.parsed_commands)

    async def overmind_building_iter(self):
        game_time = self.time_formatted

        current_units = self.get_units_all()
        print("[Building] our units:", current_units)

        current_buildings = self.get_buildings_all()
        print("[Building] our buildings:", current_buildings)

        tmp_current_enemy_units = []
        current_enemy_units = self.get_enemy_units()
        if current_enemy_units == "":
            current_enemy_units = self.previous_enemy_units
        self.previous_enemy_units = current_enemy_units

        for location, units_summary in current_enemy_units.items():
            if self.start_location_label == "B1":
                location = location.replace('A', 'B')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_enemy_units.append(f"At point {location}, there are: {units_summary}")

        tmp_current_enemy_buildings = []
        current_enemy_buildings = self.get_enemy_buildings()
        if current_enemy_buildings == "":
            current_enemy_buildings = self.previous_enemy_buildings
        self.previous_enemy_buildings = current_enemy_buildings
        print("enemy buildings:")
        for location, units_summary in current_enemy_buildings.items():
            if self.start_location_label == "B1":
                location = location.replace('A', 'B')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_enemy_buildings.append(f"At point {location}, there are: {units_summary}")

        print("[Building] previous_commands:", self.previous_commands)
        output = await overmind_building_iter(game_time, current_units, current_buildings,
                                              tmp_current_enemy_units,
                                              tmp_current_enemy_buildings, self.previous_commands)
        print(output)

        # self.game_stage = self.detect_stage(output)

        matches = re.findall(r'\(.*?\)->\(.*?\)->\(.*?\)', output)

        temp_commands = []
        for match in matches:
            temp_commands.append(match)

        self.previous_commands = temp_commands

        temp_commands = self.filter_commands(temp_commands,
                                             ['Queen', 'Gather minerals', 'Extractor', 'Mineral', 'Overlord', 'Move',
                                              'Zergling', 'Creep'])

        temp_commands_reverse = []
        if self.start_location_label == "A1":
            temp_commands_reverse = temp_commands
        elif self.start_location_label == "B1":
            for command in temp_commands:
                def replace(match):
                    char, num = match.group(1), match.group(2)
                    return 'B' + num if char == 'A' else 'A' + num

                command = re.sub(r'(A|B)(\d+)', replace, command)
                temp_commands_reverse.append(command)

        pattern = re.compile(r'\(([^)]+)\)')

        for command in temp_commands_reverse:
            parts = pattern.findall(command)
            self.parsed_commands.append(parts)

        print("self.parsed_commands:", self.parsed_commands)

    async def can_attack(self, location):
        enemy_units_at_location = self.enemy_units.closer_than(15, location)
        return enemy_units_at_location.exists

    async def llm_attack_enemy(self):
        if self.is_attack_command_issued:
            pass
        else:
            if self.start_location_label == "A1":
                enemy_base_list = ["B2", "B4", "B1", "B3"]
                rally_point = Point2(self.mineral_location_labels_reverse["B7"])
            elif self.start_location_label == "B1":
                enemy_base_list = ["A2", "A4", "A1", "A3"]
                rally_point = Point2(self.mineral_location_labels_reverse["A7"])

            avenager_units_types = [
                UnitTypeId.ZERGLING, UnitTypeId.ROACH,
                UnitTypeId.RAVAGER, UnitTypeId.BANELING, UnitTypeId.HYDRALISK, UnitTypeId.INFESTOR,
                UnitTypeId.SWARMHOSTMP, UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR, UnitTypeId.VIPER,
                UnitTypeId.ULTRALISK, UnitTypeId.BROODLORD
            ]
            defensive_units = self.units.filter(lambda unit: unit.type_id in avenager_units_types)

            for enemy_base_label in enemy_base_list:
                print("enemy_base_label:", enemy_base_label)
                enemy_base_location = Point2(self.mineral_location_labels_reverse[enemy_base_label])

                if await self.can_attack(enemy_base_location):
                    for defender in defensive_units:
                        defender.attack(enemy_base_location)
                    self.is_attack_command_issued = True
                    break

            if not self.is_attack_command_issued:
                for defender in defensive_units:
                    defender.move(rally_point)

    async def overmind_attack_iter(self):
        print("overmind_attack_iter")
        game_time = self.time_formatted

        current_units, army_damage = self.get_units_all_attack()
        print("[Attack] our units:", current_units)

        current_enemy_units_attack, enemy_damage = self.get_enemy_units_all()
        if current_enemy_units_attack == "":
            current_enemy_units_attack = self.previous_enemy_units_attack
        self.previous_enemy_units_attack = current_enemy_units_attack
        print("enemy units:", current_enemy_units_attack)
        if enemy_damage == 0:
            enemy_damage = self.previous_enemy_damage
        self.previous_enemy_damage = enemy_damage

        tmp_current_enemy_buildings = []
        current_enemy_buildings = self.get_enemy_buildings()
        if current_enemy_buildings == "":
            current_enemy_buildings = self.previous_enemy_buildings
        self.previous_enemy_buildings = current_enemy_buildings
        print("enemy buildings:")
        for location, units_summary in current_enemy_buildings.items():
            if self.start_location_label == "B1":
                location = location.replace('A', 'B')
            print(f"At point {location}, there are: {units_summary}")
            tmp_current_enemy_buildings.append(f"At point {location}, there are: {units_summary}")

        output = await overmind_attack_module(game_time, current_units, army_damage, current_enemy_units_attack,
                                              tmp_current_enemy_buildings, enemy_damage)
        print(output)

        if "True" in output:
            print("Need to attack")
            avenager_units_types = [
                UnitTypeId.ZERGLING, UnitTypeId.ROACH,
                UnitTypeId.RAVAGER, UnitTypeId.BANELING, UnitTypeId.HYDRALISK, UnitTypeId.INFESTOR,
                UnitTypeId.SWARMHOSTMP, UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR, UnitTypeId.VIPER,
                UnitTypeId.ULTRALISK, UnitTypeId.BROODLORD
            ]
            avenager_units = self.units.filter(
                lambda unit: unit.type_id in avenager_units_types
            )
            for avenager in avenager_units:
                avenager.attack(self.enemy_start_locations[0])
            # await self.llm_attack_enemy()
        else:
            print("Do not Need to attack! Retreat to base")
            if self.start_location_label == 'A1':
                if 'A3' in self.existing_hatchery_locations:
                    retreat_base = 'A3'
                else:
                    retreat_base = self.existing_hatchery_locations[-1]
            elif self.start_location_label == 'B1':
                if 'B3' in self.existing_hatchery_locations:
                    retreat_base = 'B3'
                else:
                    retreat_base = self.existing_hatchery_locations[-1]
            retreat_point = Point2(self.mineral_location_labels_reverse[retreat_base])
            avenager_units_types = [
                UnitTypeId.ZERGLING, UnitTypeId.ROACH,
                UnitTypeId.RAVAGER, UnitTypeId.BANELING, UnitTypeId.HYDRALISK, UnitTypeId.INFESTOR,
                UnitTypeId.SWARMHOSTMP, UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR, UnitTypeId.VIPER,
                UnitTypeId.ULTRALISK, UnitTypeId.BROODLORD
            ]
            defensive_units = self.units.filter(
                lambda unit: unit.type_id in avenager_units_types
            )
            for defender in defensive_units:
                defender.move(retreat_point)

            self.is_attack_command_issued = False

    def get_units_around_location(self, location, radius):
        units_around = [unit for unit in self.units if self.distance(unit.position, location) < radius]
        return len(units_around)

    def distance(self, point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

    def count_units_around_minerals(self):
        check_radius = 10
        if self.start_location_label == "A1":
            enemy_mineral_positions = ["B1", "B2", "B3", "B4"]
        elif self.start_location_label == "B1":
            enemy_mineral_positions = ["A1", "A2", "A3", "A4"]

        units_count_around_minerals = {}
        count_all = 0
        for label in enemy_mineral_positions:
            location = self.mineral_location_labels_reverse[label]
            count = self.get_units_around_location(location, check_radius)
            units_count_around_minerals[label] = count
            count_all += count
        return units_count_around_minerals, count_all

    async def attack_enemy(self):
        if self.start_location_label == "A1":
            enemy_base_list = ["B2", "B4", "B1", "B3"]
            point1 = Point2(self.mineral_location_labels_reverse["B3"])
            rally_point = point1.position.to2.towards(self.game_info.map_center, 10.0)
        elif self.start_location_label == "B1":
            enemy_base_list = ["A2", "A4", "A1", "A3"]
            point1 = Point2(self.mineral_location_labels_reverse["A3"])
            rally_point = point1.position.to2.towards(self.game_info.map_center, 10.0)

        avenger_units_types = [
            UnitTypeId.ZERGLING, UnitTypeId.OVERSEER, UnitTypeId.ROACH,
            UnitTypeId.RAVAGER, UnitTypeId.BANELING, UnitTypeId.HYDRALISK, UnitTypeId.INFESTOR,
            UnitTypeId.SWARMHOSTMP, UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR, UnitTypeId.VIPER,
            UnitTypeId.ULTRALISK, UnitTypeId.BROODLORD
        ]

        _, count_all = self.count_units_around_minerals()
        if count_all > 10:
            rally_point = self.enemy_start_locations[0]

        avenger_units = self.units.filter(lambda unit: unit.type_id in avenger_units_types)
        total_avenger_units = avenger_units.amount

        if total_avenger_units == 0:
            return

        units_at_rally_point = avenger_units.closer_than(10, rally_point).amount  # 假设的最接近距离，根据需要进行调整

        required_ratio = 0.75

        if units_at_rally_point / total_avenger_units >= required_ratio:
            for avenger in avenger_units:
                avenger.attack(Point2(self.mineral_location_labels_reverse[enemy_base_list[0]]))
        else:
            for avenger in avenger_units:
                if avenger.distance_to(rally_point) > 10:
                    avenger.move(rally_point)

    async def detect_enemy_invasion(self):
        if self.start_location_label == "A1":
            enemy_base_list = ["B2", "B4", "B1", "B3"]
            rally_point = Point2(self.mineral_location_labels_reverse["B7"])
        elif self.start_location_label == "B1":
            enemy_base_list = ["A2", "A4", "A1", "A3"]
            rally_point = Point2(self.mineral_location_labels_reverse["A7"])

        enemy_close_distance = 20
        chase_limit = 30

        defensive_units_types = [
            UnitTypeId.QUEEN, UnitTypeId.ZERGLING, UnitTypeId.OVERSEER, UnitTypeId.ROACH,
            UnitTypeId.RAVAGER, UnitTypeId.BANELING, UnitTypeId.HYDRALISK, UnitTypeId.INFESTOR,
            UnitTypeId.SWARMHOSTMP, UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR, UnitTypeId.VIPER,
            UnitTypeId.ULTRALISK, UnitTypeId.BROODLORD
        ]
        counterattack_units_types = [
            UnitTypeId.ZERGLING, UnitTypeId.OVERSEER, UnitTypeId.ROACH,
            UnitTypeId.RAVAGER, UnitTypeId.BANELING, UnitTypeId.HYDRALISK, UnitTypeId.INFESTOR,
            UnitTypeId.SWARMHOSTMP, UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR, UnitTypeId.VIPER,
            UnitTypeId.ULTRALISK, UnitTypeId.BROODLORD
        ]

        base_count = self.townhalls.amount
        no_enemy_count = 0
        for hatchery in self.townhalls:
            close_enemies = self.enemy_units.closer_than(
                enemy_close_distance, hatchery.position).exclude_type(UnitTypeId.SCV)
            if close_enemies.exists:
                self.attack_wave += 1
                hatchery_label = self.mineral_location_labels.get(hatchery.position)
                print("Detect enemy around", hatchery_label)
                self.base_being_attacked = True

                defensive_units = self.units.filter(
                    lambda unit: unit.type_id in defensive_units_types
                )

                for defender in defensive_units:
                    closest_enemy = close_enemies.closest_to(defender)
                    if defender.distance_to(closest_enemy) < chase_limit:
                        defender.attack(closest_enemy)
                    else:
                        defender.move(hatchery.position)
                    self.defence = True

            else:
                no_enemy_count += 1

            if no_enemy_count == base_count:
                if not self.defence and not self.fight_back:
                    if self.base_being_attacked:
                        print("Enemy has been defeated.")
                        print("Whether we should counterattack:", self.counterattack)
                        self.fight_back = True
                        defensive_units = self.units.filter(lambda unit: unit.type_id in counterattack_units_types)
                        for defender in defensive_units:
                            defender.attack(Point2(self.mineral_location_labels_reverse[enemy_base_list[0]]))
                        self.base_being_attacked = False
                elif self.defence:
                    self.defence = False

    async def early_game_production(self):
        await self.Drone_ReflexNet()
        if self.early_zergling_num != 0:
            await self.Zergling_ReflexNet()
        if self.early_roach_num != 0:
            await self.Roach_ReflexNet()

    async def mid_game_production(self):
        await self.Drone_ReflexNet()
        if self.mid_roach_num != 0:
            await self.Roach_ReflexNet()
        if self.mid_ravager_num != 0:
            await self.Ravager_ReflexNet()
        if self.mid_hydralisk_num != 0:
            await self.Hydralisk_ReflexNet()
        if self.mid_zergling_num != 0:
            await self.Zergling_ReflexNet()

    async def late_game_production(self):
        if self.minerals < 1000:
            await self.Drone_ReflexNet()
        if self.late_roach_num != 0:
            await self.Roach_ReflexNet()
        if self.late_ravager_num != 0:
            await self.Ravager_ReflexNet()
        if self.late_zergling_num != 0:
            await self.Zergling_ReflexNet()
        if self.late_ultralisk_num != 0:
            await self.Ultralisk_ReflexNet()
        if self.late_hydralisk_num != 0:
            await self.Hydralisk_ReflexNet()
        if self.late_corruptor_num != 0:
            await self.Corruptor_ReflexNet()
        # await self.infestor_ReflexNet()

    async def morphing(self):
        if self.waiting_for_hatchery == True and self.minerals <= 400:
            print("No morphing due to waiting_for_hatchery")
            return

        # print("morphing")
        # Roach
        if self.structures(UnitTypeId.ROACHWARREN).ready.exists:
            if self.game_stage == 0:  # Early Stage
                roach_thre = self.early_roach_num
                if self.units(UnitTypeId.ROACH).amount < self.early_roach_num:
                    if self.can_afford(UnitTypeId.ROACH) and self.units(UnitTypeId.LARVA).exists:
                        larva = self.units(UnitTypeId.LARVA).random
                        larva.train(UnitTypeId.ROACH)
                        print("early larva.train(UnitTypeId.ROACH)")
            elif self.game_stage == 1:  # Mid Stage
                roach_thre = self.mid_roach_num
                if self.units(UnitTypeId.ROACH).amount < self.mid_roach_num:
                    if self.can_afford(UnitTypeId.ROACH) and self.units(UnitTypeId.LARVA).exists:
                        larva = self.units(UnitTypeId.LARVA).random
                        larva.train(UnitTypeId.ROACH)
                        print("mid larva.train(UnitTypeId.ROACH)")
            elif self.game_stage == 2:  # Late Stage
                roach_thre = self.late_roach_num
                if self.units(UnitTypeId.ROACH).amount < self.late_roach_num:
                    if self.can_afford(UnitTypeId.ROACH) and self.units(UnitTypeId.LARVA).exists:
                        larva = self.units(UnitTypeId.LARVA).random
                        larva.train(UnitTypeId.ROACH)
                        print("late larva.train(UnitTypeId.ROACH)")

        # Ravager
        if self.can_afford(UnitTypeId.RAVAGER) and self.units(UnitTypeId.ROACH).exists and self.supply_left > 0:
            if self.game_stage == 0:  # Early Stage
                if self.units(UnitTypeId.RAVAGER).amount < self.early_ravager_num:
                    roach = self.units(UnitTypeId.ROACH).ready.idle
                    if roach.exists:
                        roach.random(AbilityId.MORPHTORAVAGER_RAVAGER)
            elif self.game_stage == 1:  # Mid Stage
                if self.units(UnitTypeId.RAVAGER).amount < self.mid_ravager_num:
                    roach = self.units(UnitTypeId.ROACH).ready.idle
                    if roach.exists:
                        roach.random(AbilityId.MORPHTORAVAGER_RAVAGER)
            elif self.game_stage == 2:  # Late Stage
                if self.units(UnitTypeId.ROACH).amount < self.late_ravager_num:
                    roach = self.units(UnitTypeId.ROACH).ready.idle
                    if roach.exists:
                        roach.random(AbilityId.MORPHTORAVAGER_RAVAGER)

        # Hydralisk
        if self.structures(UnitTypeId.HYDRALISKDEN).ready.exists:
            if self.game_stage == 0:
                hydralisk_num = self.early_hydralisk_num
            elif self.game_stage == 1:
                hydralisk_num = self.mid_hydralisk_num
            elif self.game_stage == 2:
                hydralisk_num = self.late_hydralisk_num
            if self.units(UnitTypeId.HYDRALISK).amount < hydralisk_num:
                if self.can_afford(UnitTypeId.HYDRALISK) and self.units(UnitTypeId.LARVA).exists:
                    larva = self.units(UnitTypeId.LARVA).random
                    larva.train(UnitTypeId.HYDRALISK)
                    print("train hydralisk")

        # Zergling
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists:
            if self.game_stage == 0:  # Early Stage
                if self.units(UnitTypeId.ZERGLING).amount < self.early_zergling_num:
                    if self.can_afford(UnitTypeId.ZERGLING) and self.units(UnitTypeId.LARVA).exists:
                        larva = self.units(UnitTypeId.LARVA).random
                        larva.train(UnitTypeId.ZERGLING)
                        print("early larva.train(UnitTypeId.ZERGLING)")
            elif self.game_stage == 1:  # Mid Stage
                if self.units(UnitTypeId.ZERGLING).amount < self.mid_zergling_num:
                    if self.can_afford(UnitTypeId.ZERGLING) and self.units(UnitTypeId.LARVA).exists:
                        larva = self.units(UnitTypeId.LARVA).random
                        larva.train(UnitTypeId.ZERGLING)
                        print("mid larva.train(UnitTypeId.ZERGLING)")
            elif self.game_stage == 2:  # Late Stage
                if self.units(UnitTypeId.ZERGLING).amount < self.late_zergling_num:
                    if self.can_afford(UnitTypeId.ZERGLING) and self.units(UnitTypeId.LARVA).exists:
                        larva = self.units(UnitTypeId.LARVA).random
                        larva.train(UnitTypeId.ZERGLING)
                        print("late larva.train(UnitTypeId.ZERGLING)")

        # Baneling
        if self.structures(UnitTypeId.BANELINGNEST).ready.exists and self.supply_left > 0 and self.can_afford(
                UnitTypeId.BANELING):
            if self.game_stage == 0:  # Early Stage
                if self.units(UnitTypeId.BANELING).amount < self.early_baneling_num:
                    zergling = self.units(UnitTypeId.ZERGLING).ready.idle
                    if zergling.exists:
                        zergling.random(AbilityId.MORPHTOBANELING_BANELING)
            elif self.game_stage == 1:  # Mid Stage
                if self.units(UnitTypeId.BANELING).amount < self.mid_baneling_num:
                    zergling = self.units(UnitTypeId.ZERGLING).ready.idle
                    if zergling.exists:
                        zergling.random(AbilityId.MORPHTOBANELING_BANELING)
            elif self.game_stage == 2:  # Late Stage
                if self.units(UnitTypeId.BANELING).amount < self.late_baneling_num:
                    zergling = self.units(UnitTypeId.ZERGLING).ready.idle
                    if zergling.exists:
                        zergling.random(AbilityId.MORPHTOBANELING_BANELING)

        # Ultralisk
        if self.structures(UnitTypeId.ULTRALISKCAVERN).ready.exists:
            ultralisk_num = 0
            if self.game_stage == 0:
                ultralisk_num = self.early_ultralisk_num
            elif self.game_stage == 1:
                ultralisk_num = self.mid_ultralisk_num
            elif self.game_stage == 2:
                ultralisk_num = self.late_ultralisk_num

            if self.units(UnitTypeId.ULTRALISK).amount < ultralisk_num:
                if self.units(UnitTypeId.LARVA).exists:
                    larva = self.units(UnitTypeId.LARVA).random
                    larva.train(UnitTypeId.ULTRALISK)

        # Corruptor
        if self.structures(UnitTypeId.SPIRE).ready.exists:
            corruptor_num = 0
            if self.game_stage == 0:
                corruptor_num = self.early_corruptor_num
            elif self.game_stage == 1:
                corruptor_num = self.mid_corruptor_num
            elif self.game_stage == 2:
                corruptor_num = self.late_corruptor_num
            if self.units(UnitTypeId.CORRUPTOR).amount <= corruptor_num:
                if self.can_afford(UnitTypeId.CORRUPTOR) and self.units(UnitTypeId.LARVA).exists:
                    larva = self.units(UnitTypeId.LARVA).random
                    larva.train(UnitTypeId.CORRUPTOR)

    async def on_step(self, iteration: int):
        # if self.enemy_units:
        #     await self.client.debug_kill_unit(self.enemy_units)

        await self.Drone_ReflexNet()
        await self.morphing()

        await self.Queen_ReflexNet()
        await self.distribute_workers()
        await self.auto_build_extractors()
        await self.auto_research()
        await self.queen_spread()

        await self.Ravager_ReflexNet()

        if self.id_game_stage() == 0:
            self.game_stage = 0
            await self.early_game_production()
        elif self.id_game_stage() == 1:
            self.game_stage = 1
            await self.mid_game_production()
        elif self.id_game_stage() == 2:
            self.game_stage = 2
            await self.late_game_production()

        await self.Overlord_ReflexNet()
        await self.handle_commands()
        await self.detect_enemy_invasion()

        if iteration % 60 == 0:
            if len(self.parsed_commands) < 10:
                building_task = asyncio.create_task(self.overmind_building_iter())
                self.building_tasks.append(building_task)

            finished_tasks = [task for task in self.building_tasks if task.done()]
            for task in finished_tasks:
                result = task.result()
                print("building result:", result)
                self.building_tasks.remove(task)

        if iteration % 150 == 0:
            if self.army_count > 15:
                attack_tasks = asyncio.create_task(self.overmind_attack_iter())
                self.attack_tasks.append(attack_tasks)

                finished_tasks = [task for task in self.attack_tasks if task.done()]
                for task in finished_tasks:
                    result = task.result()
                    print("attack result:", result)
                    self.attack_tasks.remove(task)

    def time_exceeds(self, minutes):
        minutes_passed, seconds_passed = map(int, self.time_formatted.split(':'))
        total_seconds_passed = (minutes_passed * 60) + seconds_passed

        threshold_seconds = minutes * 60

        return total_seconds_passed > threshold_seconds

    async def build_buildings(self, name, i, location):
        if "Drone" in name:
            if i < len(self.parsed_commands):
                del self.parsed_commands[i]
                return

        if "Hatchery" in name:
            print("Hatchery in name")
            if self.can_afford(UnitTypeId.HATCHERY):
                pos = Point2(self.mineral_location_labels_reverse[location])
                if not self.time_exceeds(4) and self.army_count <= 15 and self.townhalls.amount == 2:
                    return
                if await self.can_place(UnitTypeId.HATCHERY, pos):
                    success = self.workers.collecting.random.build(UnitTypeId.HATCHERY, pos)
                    if success:
                        self.waiting_for_hatchery = False
                        print("self.waiting_for_hatchery set to False")
                        if i < len(self.parsed_commands):
                            del self.parsed_commands[i]
                        return
                else:
                    print("cannot place Hatchery!", location)
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Spawning Pool" in name:
            # print("Spawning Pool in name")
            if self.already_pending(UnitTypeId.SPAWNINGPOOL):
                print("SPAWNINGPOOL in pending")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return
            # print("Already have SPAWNINGPOOL:", self.structures(UnitTypeId.SPAWNINGPOOL).amount)
            if self.structures(UnitTypeId.SPAWNINGPOOL).amount >= 1:
                # print("Already have SPAWNINGPOOL:", self.structures(UnitTypeId.SPAWNINGPOOL).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

            if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)

                placement_position = await self.find_placement(UnitTypeId.SPAWNINGPOOL,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.SPAWNINGPOOL, placement_position)
                # print("Build success:", success)
                if success:
                    # print("Successfully built Spawning Pool")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return


        elif "Evolution Chamber" in name:
            if self.already_pending(UnitTypeId.EVOLUTIONCHAMBER):
                # print("Evolution Chamber in pending")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return
            # print("Already have EVOLUTIONCHAMBER:", self.structures(UnitTypeId.EVOLUTIONCHAMBER).amount)
            if self.structures(UnitTypeId.EVOLUTIONCHAMBER).amount >= 1:
                # print("Already have EVOLUTIONCHAMBER:", self.structures(UnitTypeId.EVOLUTIONCHAMBER).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return
            if self.can_afford(UnitTypeId.EVOLUTIONCHAMBER) and self.structures(
                    UnitTypeId.SPAWNINGPOOL).exists and not self.structures(
                UnitTypeId.EVOLUTIONCHAMBER).ready.exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)
                placement_position = await self.find_placement(UnitTypeId.EVOLUTIONCHAMBER,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.EVOLUTIONCHAMBER, placement_position)
                # print("Build success:", success)
                if success:
                    # print("Successfully built Evolution Chamber")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        if self.waiting_for_hatchery == True:
            return

        if "Extractor" in name:
            # print("Extractor in name")
            if self.can_afford(UnitTypeId.EXTRACTOR):
                base_location = Point2(self.mineral_location_labels_reverse[location])
                if self.townhalls.closer_than(2.0, base_location).ready.exists:
                    hatchery = self.townhalls.closer_than(2.0, base_location).ready.first
                    for vg in self.vespene_geyser.closer_than(10, hatchery):
                        drone: Unit = self.workers.random
                        drone.build_gas(vg)
                        # print("Successfully built gas")
                        if i < len(self.parsed_commands):
                            del self.parsed_commands[i]
                            # print("Deleted command_list at index", i)
                        break

        elif "Spine Crawler" in name:
            if self.can_afford(UnitTypeId.SPINECRAWLER):
                base_location = Point2(self.mineral_location_labels_reverse[location])
                spine_near_townhall = self.structures(UnitTypeId.SPINECRAWLER).closer_than(15, base_location).amount
                if spine_near_townhall >= 1:
                    # print("Already have SPINECRAWLER:", spine_near_townhall)
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return
                next_place = self.game_info.map_center
                if self.start_location_label == "A1":
                    next_place = Point2(self.mineral_location_labels_reverse["A2"])
                elif self.start_location_label == "B1":
                    next_place = Point2(self.mineral_location_labels_reverse["B2"])

                pos = base_location.position.to2.towards(next_place, 5.0)
                placement_position = await self.find_placement(UnitTypeId.SPINECRAWLER,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.SPINECRAWLER, placement_position)
                if success:
                    # print("Successfully built Spine Crawler")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Spore Crawler" in name:
            if self.can_afford(UnitTypeId.SPORECRAWLER):
                # Don't want too many spore crawler around base
                base_location = Point2(self.mineral_location_labels_reverse[location])
                spore_near_townhall = self.structures(UnitTypeId.SPORECRAWLER).closer_than(15, base_location).amount
                if spore_near_townhall >= 1:
                    # print("Already have SPORECRAWLER:", spore_near_townhall)
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)
                placement_position = await self.find_placement(UnitTypeId.SPORECRAWLER,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.SPORECRAWLER, placement_position)
                if success:
                    # print("Successfully built Spore Crawler")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        if not self.time_exceeds(5):
            return

        elif "Lair" in name:
            # print("Lair in name")
            if self.can_afford(UnitTypeId.LAIR):
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])

                hatchery = self.townhalls.closer_than(2.0, base_location).ready.first
                success = hatchery.build(UnitTypeId.LAIR)
                if success:
                    # print("Successfully built Lair")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Roach Warren" in name:
            if self.already_pending(UnitTypeId.ROACHWARREN):
                # print("ROACHWARREN is already pending")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return
            if self.structures(UnitTypeId.ROACHWARREN).amount >= 1:
                # print("Already have ROACHWARREN:", self.structures(UnitTypeId.ROACHWARREN).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return
            if self.can_afford(UnitTypeId.ROACHWARREN) and not self.structures(
                    UnitTypeId.ROACHWARREN).ready.exists and self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)
                placement_position = await self.find_placement(UnitTypeId.ROACHWARREN,
                                                               near=pos)

                if await self.can_place_single(UnitTypeId.ROACHWARREN, placement_position):
                    drone: Unit = self.workers.closest_to(placement_position)
                    success = drone.build(UnitTypeId.ROACHWARREN, placement_position)
                    if success:
                        # print("Successfully built Roach Warren")
                        if i < len(self.parsed_commands):
                            del self.parsed_commands[i]
                        return


        elif "Baneling Nest" in name:
            if self.structures(UnitTypeId.BANELINGNEST).amount >= 1 and self.already_pending(UnitTypeId.BANELINGNEST):
                # print("Already have BANELINGNEST:", self.structures(UnitTypeId.BANELINGNEST).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

            if self.can_afford(UnitTypeId.BANELINGNEST) and not self.structures(
                    UnitTypeId.BANELINGNEST).exists and not self.already_pending(UnitTypeId.BANELINGNEST):
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)
                placement_position = await self.find_placement(UnitTypeId.BANELINGNEST,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.BANELINGNEST, placement_position)
                if success:
                    # print("Successfully built Baneling Nest")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Hydralisk" in name:
            if self.structures(UnitTypeId.HYDRALISKDEN).amount >= 1:
                # print("Already have HYDRALISKDEN:", self.structures(UnitTypeId.HYDRALISKDEN).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

            if self.can_afford(UnitTypeId.HYDRALISKDEN) and not self.structures(
                    UnitTypeId.HYDRALISKDEN).ready.exists and self.townhalls(UnitTypeId.LAIR).ready.exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)
                placement_position = await self.find_placement(UnitTypeId.HYDRALISKDEN,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.HYDRALISKDEN, placement_position)
                if success:
                    # print("Successfully built Hydralisk den")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Infestation Pit" in name:
            if self.structures(UnitTypeId.INFESTATIONPIT).amount >= 1:
                # print("Already have INFESTATIONPIT:", self.structures(UnitTypeId.INFESTATIONPIT).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

            if not self.townhalls(UnitTypeId.LAIR).ready.exists and not self.already_pending(UnitTypeId.LAIR):
                if self.can_afford(UnitTypeId.LAIR):
                    hatchery = self.townhalls(UnitTypeId.HATCHERY).ready.first
                    success = hatchery.build(UnitTypeId.LAIR)

            if self.can_afford(UnitTypeId.INFESTATIONPIT) and not self.structures(
                    UnitTypeId.INFESTATIONPIT).ready.exists and self.townhalls(UnitTypeId.LAIR).ready.exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 5.0)
                placement_position = await self.find_placement(UnitTypeId.ROACHWARREN,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.INFESTATIONPIT, placement_position)
                if success:
                    # print("Successfully built Infestation Pit")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Spire" in name:
            if self.structures(UnitTypeId.SPIRE).amount >= 1 and not self.already_pending(UnitTypeId.SPIRE):
                # print("Already have SPIRE:", self.structures(UnitTypeId.SPIRE).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

            if self.can_afford(UnitTypeId.SPIRE) and not self.structures(
                    UnitTypeId.SPIRE).exists and self.townhalls(UnitTypeId.LAIR).ready.exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                pos = base_location.position.to2.towards(self.game_info.map_center, 6.0)
                placement_position = await self.find_placement(UnitTypeId.SPIRE,
                                                               near=pos)

                success = self.workers.collecting.random.build(UnitTypeId.SPIRE, placement_position)
                if success:
                    # print("Successfully built Spire")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        # print("self.time_exceeds(10):", self.time_exceeds(10))
        if not self.time_exceeds(10):
            return

        elif "Hive" in name:
            # print("Hive in name")
            if self.can_afford(UnitTypeId.HIVE) and self.structures(
                    UnitTypeId.LAIR).ready.exists and self.structures(UnitTypeId.INFESTATIONPIT).ready.exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                hatchery = self.townhalls.closer_than(2.0, base_location).ready.first
                success = hatchery.build(UnitTypeId.HIVE)
                if success:
                    # print("Successfully built Hive")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Ultralisk Cavern" in name:
            if self.townhalls(UnitTypeId.LAIR).exists:
                if not self.townhalls(UnitTypeId.HIVE).ready.exists and not self.already_pending(UnitTypeId.HIVE):
                    if self.can_afford(UnitTypeId.HIVE):
                        lair = self.townhalls(UnitTypeId.LAIR).ready.first
                        success = lair.build(UnitTypeId.HIVE)
            else:
                if self.can_afford(UnitTypeId.LAIR):
                    if self.start_location_label == "A1":
                        base_location = Point2(self.mineral_location_labels_reverse["A1"])
                    elif self.start_location_label == "B1":
                        base_location = Point2(self.mineral_location_labels_reverse["B1"])

                    hatchery = self.townhalls.closer_than(2.0, base_location).ready.first
                    success = hatchery.build(UnitTypeId.LAIR)
                    if success:
                        print("build Lair success")

            if self.structures(UnitTypeId.ULTRALISKCAVERN).amount >= 1:
                # print("Already have ULTRALISKCAVERN:", self.structures(UnitTypeId.ULTRALISKCAVERN).amount)
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

            if self.can_afford(UnitTypeId.ULTRALISKCAVERN) and self.townhalls(
                    UnitTypeId.HIVE).ready.exists and not self.structures(UnitTypeId.ULTRALISKCAVERN).exists:
                if self.start_location_label == "A1":
                    base_location = Point2(self.mineral_location_labels_reverse["A1"])
                elif self.start_location_label == "B1":
                    base_location = Point2(self.mineral_location_labels_reverse["B1"])
                if self.start_location_label == "A1":
                    next_place = Point2(self.mineral_location_labels_reverse["A2"])
                elif self.start_location_label == "B1":
                    next_place = Point2(self.mineral_location_labels_reverse["B2"])
                pos2 = base_location.position.to2.towards(next_place, 5.0)
                placement_position = await self.find_placement(UnitTypeId.ULTRALISKCAVERN,
                                                               near=pos2)

                success = self.workers.collecting.random.build(UnitTypeId.ULTRALISKCAVERN, placement_position)
                if success:
                    # print("Successfully built Ultralisk Cavern")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        elif "Greater Spire" in name:
            if not self.townhalls(UnitTypeId.HIVE).ready.exists and not self.already_pending(UnitTypeId.HIVE):
                if self.can_afford(UnitTypeId.HIVE) and self.townhalls(UnitTypeId.LAIR).exists:
                    lair = self.townhalls(UnitTypeId.LAIR).ready.first
                    success = lair.build(UnitTypeId.HIVE)
                    if success:
                        print("Build Hive")

            if self.can_afford(UnitTypeId.GREATERSPIRE) and self.structures(UnitTypeId.SPIRE).ready.exists:
                spire = self.structures(UnitTypeId.SPIRE).ready.first
                success = spire.build(UnitTypeId.GREATERSPIRE)
                if success:
                    print("Build Greater Spire")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return


        else:
            if i < len(self.parsed_commands):
                del self.parsed_commands[i]
            return

    async def build_units(self, name, i):
        if "Drone" in name:
            # print("build drone")
            if self.can_afford(UnitTypeId.DRONE) and self.units(UnitTypeId.LARVA).exists:
                larva = self.units(UnitTypeId.LARVA).random
                larva.train(UnitTypeId.DRONE)

                # print("Successfully built Drone")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]

        elif "Zergling" in name:
            if self.can_afford(UnitTypeId.ZERGLING) and self.structures(
                    UnitTypeId.SPAWNINGPOOL).ready.exists and self.units(
                UnitTypeId.LARVA).exists:
                larva = self.units(UnitTypeId.LARVA).random
                larva.train(UnitTypeId.ZERGLING)

                # print("Successfully built Zergling")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

        elif "Roach" in name:
            if self.can_afford(UnitTypeId.ROACH) and self.structures(
                    UnitTypeId.ROACHWARREN).ready.exists and self.units(
                UnitTypeId.LARVA).exists:
                larva = self.units(UnitTypeId.LARVA).random
                larva.train(UnitTypeId.ROACH)

                # print("Successfully built Roach")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

        elif "Ravager" in name:
            if self.can_afford(UnitTypeId.RAVAGER) and self.units(UnitTypeId.ROACH).exists and self.supply_left > 0:
                roach = self.units(UnitTypeId.ROACH).ready.idle
                if roach.exists:
                    roach.random(AbilityId.MORPHTORAVAGER_RAVAGER)

        elif "Hydralisk" in name:
            if self.can_afford(UnitTypeId.HYDRALISK) and self.structures(
                    UnitTypeId.HYDRALISKDEN).ready.exists and self.units(UnitTypeId.LARVA).exists:
                larva = self.units(UnitTypeId.LARVA).random
                larva.train(UnitTypeId.HYDRALISK)

                # print("Successfully built Hydralisk")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

    def check_loc(self, input_str):
        loc_list = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]
        for loc in loc_list:
            if loc in input_str:
                return loc
        return ""

    def find_safety(self, position):
        friendly_location = min(self.structures.ready,
                                key=lambda unit: unit.position.distance_to(position)).position
        return friendly_location

    async def Drone_ReflexNet(self):
        # print("Drone_ReflexNet")
        await self.autocreating_drones()

        for drone in self.workers.idle:
            if self.townhalls.ready.exists:
                closest_hatchery = self.townhalls.ready.closest_to(drone)
                closest_minerals = self.mineral_field.closer_than(30, closest_hatchery).closest_to(closest_hatchery)
                drone.gather(closest_minerals)

        for drone in self.workers:
            threats = self.enemy_units.closer_than(5, drone)
            if threats:
                # print("Drone detected enemy!")
                no_threats = threats.filter(lambda unit: unit.can_attack_ground and unit.type_id == UnitTypeId.SCV)
                low_threats = threats.filter(lambda unit: unit.can_attack_ground and unit.type_id == UnitTypeId.MARINE)
                high_threats = threats.filter(
                    lambda
                        unit: unit.can_attack_ground and unit.type_id != UnitTypeId.MARINE and unit.type_id != UnitTypeId.SCV)
                if self.worker_aggressive == False:
                    if low_threats.amount > 0 and low_threats.amount <= 2:
                        for d in self.workers.closer_than(5, drone):
                            d.attack(low_threats.closest_to(d))

                    if high_threats.exists:
                        enemy_center = high_threats.center
                        for d in self.workers.closer_than(5, drone):
                            retreat_point = d.position.towards_with_random_angle(enemy_center, -5)
                            d.move(retreat_point)
                        continue

                    if not self.enemy_units.closer_than(10, drone):
                        bases = self.townhalls(UnitTypeId.HATCHERY).ready
                        if bases:
                            base = max(bases, key=lambda b: b.ideal_harvesters - b.assigned_harvesters)
                            drone.gather(self.mineral_field.closest_to(base))

                else:
                    if high_threats.exists:
                        for d in self.workers.closer_than(8, drone):
                            d.attack(high_threats.closest_to(d))

                    if low_threats.exists:
                        for d in self.workers.closer_than(8, drone):
                            d.attack(low_threats.closest_to(d))

    async def autocreating_drones(self):
        all_hatcheries = self.townhalls.ready
        mineral_fields = self.mineral_field
        drones = self.units(UnitTypeId.DRONE)

        drones_per_mineral_patch = 2

        for hatchery in all_hatcheries:
            nearby_mineral_patches = mineral_fields.closer_than(10, hatchery)
            optimal_drones = drones_per_mineral_patch * nearby_mineral_patches.amount

            hatchery_drones = drones.closer_than(10, hatchery)

            if len(hatchery_drones) < optimal_drones:
                if self.can_afford(UnitTypeId.DRONE) and self.larva:
                    self.train(UnitTypeId.DRONE, amount=3)

    async def auto_build_extractors(self):
        for hatchery in self.townhalls.ready:
            if self.workers.closer_than(10, hatchery).amount > 14:
                if self.can_afford(UnitTypeId.EXTRACTOR):
                    for vg in self.vespene_geyser.closer_than(10, hatchery):
                        drone: Unit = self.workers.random
                        drone.build_gas(vg)

    async def auto_research(self):
        if self.units(UnitTypeId.OVERLORD).amount >= 5:
            if self.can_afford(UpgradeId.OVERLORDSPEED) and self.townhalls.exists:
                self.research(UpgradeId.OVERLORDSPEED)

        if self.units(UnitTypeId.ZERGLING).amount >= 5:
            if self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists and self.can_afford(
                    UpgradeId.ZERGLINGMOVEMENTSPEED):
                self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)

        if self.units(UnitTypeId.BANELING).amount >= 4 and self.structures(
                UnitTypeId.BANELINGNEST).ready.exists and self.already_pending_upgrade(
            UpgradeId.CENTRIFICALHOOKS) == 0:
            if self.can_afford(UpgradeId.CENTRIFICALHOOKS):
                success = self.research(UpgradeId.CENTRIFICALHOOKS)
                # if not success:
                #     print("CENTRIFICALHOOKS failed:", success)

        if self.units(UnitTypeId.ZERGLING).amount >= 8 and self.structures(
                UnitTypeId.EVOLUTIONCHAMBER).ready.exists and self.already_pending_upgrade(
            UpgradeId.ZERGMELEEWEAPONSLEVEL1) == 0:
            if self.can_afford(UpgradeId.ZERGMELEEWEAPONSLEVEL1):
                success = self.research(UpgradeId.ZERGMELEEWEAPONSLEVEL1)
                # if not success:
                #     print("ZERGMELEEWEAPONSLEVEL1 failed!", success)

        if self.units(UnitTypeId.ROACH).amount >= 5 and self.structures(
                UnitTypeId.EVOLUTIONCHAMBER).ready.exists and self.already_pending_upgrade(
            UpgradeId.ZERGMISSILEWEAPONSLEVEL1) == 0:
            if self.can_afford(UpgradeId.ZERGMISSILEWEAPONSLEVEL1):
                success = self.research(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)
                # if not success:
                #     print("ZERGMISSILEWEAPONSLEVEL1 failed!", success)

        if self.units(UnitTypeId.ROACH).amount >= 8 and self.structures(
                UnitTypeId.EVOLUTIONCHAMBER).ready.exists and self.already_pending_upgrade(
            UpgradeId.ZERGGROUNDARMORSLEVEL1) == 0:
            if self.can_afford(UpgradeId.ZERGGROUNDARMORSLEVEL1):
                success = self.research(UpgradeId.ZERGGROUNDARMORSLEVEL1)
                # if not success:
                #     print("ZERGGROUNDARMORSLEVEL1 failed!", success)

        if self.structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists and self.structures(UnitTypeId.LAIR).ready.exists:
            if self.can_afford(UpgradeId.ZERGMELEEWEAPONSLEVEL2) and self.already_pending_upgrade(
                    UpgradeId.ZERGMELEEWEAPONSLEVEL2) == 0:
                success = self.research(UpgradeId.ZERGMELEEWEAPONSLEVEL2)
                # if not success:
                #     print("ZERGMELEEWEAPONSLEVEL2 failed! ", success)
            if self.can_afford(UpgradeId.ZERGMISSILEWEAPONSLEVEL2) and self.already_pending_upgrade(
                    UpgradeId.ZERGMISSILEWEAPONSLEVEL2) == 0:
                success = self.research(UpgradeId.ZERGMISSILEWEAPONSLEVEL2)
                # if not success:
                #     print("ZERGMELEEWEAPONSLEVEL2 failed!", success)
            if self.can_afford(UpgradeId.ZERGGROUNDARMORSLEVEL2) and self.already_pending_upgrade(
                    UpgradeId.ZERGGROUNDARMORSLEVEL2) == 0:
                success = self.research(UpgradeId.ZERGGROUNDARMORSLEVEL2)
                # if not success:
                #     print("ZERGGROUNDARMORSLEVEL2 failed!", success)

        if self.structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists and self.structures(UnitTypeId.HIVE).ready.exists:
            if self.can_afford(UpgradeId.ZERGMELEEWEAPONSLEVEL3) and self.already_pending_upgrade(
                    UpgradeId.ZERGMELEEWEAPONSLEVEL3) == 0:
                success = self.research(UpgradeId.ZERGMELEEWEAPONSLEVEL3)
                # if not success:
                #     print("ZERGMELEEWEAPONSLEVEL3 failed!", success)
            if self.can_afford(UpgradeId.ZERGMISSILEWEAPONSLEVEL3) and self.already_pending_upgrade(
                    UpgradeId.ZERGMISSILEWEAPONSLEVEL3) == 0:
                success = self.research(UpgradeId.ZERGMISSILEWEAPONSLEVEL3)
                # if not success:
                #     print("ZERGMISSILEWEAPONSLEVEL3 failed!", success)
            if self.can_afford(UpgradeId.ZERGGROUNDARMORSLEVEL3) and self.already_pending_upgrade(
                    UpgradeId.ZERGGROUNDARMORSLEVEL3) == 0:
                success = self.research(UpgradeId.ZERGGROUNDARMORSLEVEL3)
                # if not success:
                #     print("ZERGGROUNDARMORSLEVEL3 failed!", success)

        if self.units(UnitTypeId.ROACH).amount > 5:
            if self.can_afford(UpgradeId.GLIALRECONSTITUTION) and not self.already_pending_upgrade(
                    UpgradeId.GLIALRECONSTITUTION):
                success = self.research(UpgradeId.GLIALRECONSTITUTION)
                # if not success:
                #     print("GLIALRECONSTITUTION failed:", success)

        if self.units(UnitTypeId.HYDRALISK).amount > 5:
            if self.can_afford(UpgradeId.EVOLVEMUSCULARAUGMENTS):
                success = self.research(UpgradeId.EVOLVEMUSCULARAUGMENTS)
                if not success:
                    print("EVOLVEMUSCULARAUGMENTS failed!", success)

    async def overlord_random_scout(self, overlord):
        if overlord.is_idle:
            all_coordinates = list(self.expansion_locations.keys())
            scout_position = random.choice(all_coordinates)
            overlord.move(scout_position)

    async def Overlord_ReflexNet(self):
        if self.supply_cap < 44:
            if self.supply_left < 3 and not self.already_pending(UnitTypeId.OVERLORD):
                larvas = self.units(UnitTypeId.LARVA)
                if larvas.exists and self.can_afford(UnitTypeId.OVERLORD):
                    # print("train overlord supply_left:", self.supply_left)
                    larvas.random.train(UnitTypeId.OVERLORD)
        elif self.supply_cap >= 44 and self.supply_cap != 200:
            if self.supply_left >= 0 and self.supply_left < 5:
                larvas = self.units(UnitTypeId.LARVA)
                if larvas.exists and self.can_afford(UnitTypeId.OVERLORD):
                    # print("train overlord supply_left:", self.supply_left)
                    larvas.random.train(UnitTypeId.OVERLORD)

        for overlord in self.units(UnitTypeId.OVERLORD):
            threats = self.enemy_units.filter(lambda unit: unit.can_attack_air).closer_than(15, overlord)

            if threats:
                # self.detect_threat(threats)
                if self.base_being_attacked == False:
                    retreat_point = self.find_safety(overlord.position)
                    overlord.move(retreat_point)
                else:
                    overlord.move(self.start_location)
            else:
                await self.overlord_random_scout(overlord)

    async def overlord_scout(self, i, location):
        if location == "":
            return
        loc = Point2(self.mineral_location_labels_reverse[location])
        overlords = self.units(UnitTypeId.OVERLORD)
        if overlords.exists:
            closest_overlord = overlords.closest_to(loc)
            closest_overlord.move(loc)
            # print("Successfully move Overlord")
            if i < len(self.parsed_commands):
                del self.parsed_commands[i]
            return

    async def zergling_command(self, name, action, i, location):
        if 'baneling' in name.lower():
            if self.can_afford(UnitTypeId.BANELING) and self.structures(
                    UnitTypeId.BANELINGNEST).ready.exists and self.supply_left > 0:
                zergling = self.units(UnitTypeId.ZERGLING).ready.idle
                if zergling.exists:
                    zergling.random(AbilityId.MORPHTOBANELING_BANELING)

                    # print("Successfully morph Baneling")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        if location == "":
            return
        loc = Point2(self.mineral_location_labels_reverse[location])
        keywords = ['move', 'attack']
        if any(keyword.lower() in action.lower() for keyword in keywords):

            # await self.attack_enemy()

            # for zergling in self.units(UnitTypeId.ZERGLING).ready:
            #     zergling.attack(loc)

            # print("Successfully move Zergling")
            if i < len(self.parsed_commands):
                del self.parsed_commands[i]
            return

    async def roach_command(self, name, action, i, location):
        if 'ravager' in name.lower():
            if self.can_afford(UnitTypeId.RAVAGER) and self.structures(
                    UnitTypeId.ROACHWARREN).ready.exists and self.supply_left > 0:
                roach = self.units(UnitTypeId.ROACH).ready.idle
                if roach.exists:
                    roach.random(AbilityId.MORPHTORAVAGER_RAVAGER)

                    # print("Successfully morph Ravager")
                    if i < len(self.parsed_commands):
                        del self.parsed_commands[i]
                    return

        if location == "":
            return
        loc = Point2(self.mineral_location_labels_reverse[location])
        keywords = ['move', 'attack']
        if any(keyword.lower() in action.lower() for keyword in keywords):
            # await self.attack_enemy()
            for roach in self.units(UnitTypeId.ZERGLING).ready:
                roach.attack(loc)

                # print("Successfully move roach")
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                return

    async def Zergling_ReflexNet(self):
        # print("Zergling_ReflexNet")
        for zergling in self.units(UnitTypeId.ZERGLING).ready:
            threats = self.enemy_units.closer_than(15, zergling)
            if threats:
                # print("zergling detected enemy!")
                sigetank = threats.filter(lambda unit: unit.type_id == UnitTypeId.SIEGETANK)
                if sigetank.exists:
                    sigetank_attack = sigetank.closest_to(zergling)
                    # print("zergling attack sigetank!")
                    zergling.attack(sigetank_attack)

    async def Queen_ReflexNet(self):
        # print("Queen_ReflexNet")
        all_hatcheries = self.townhalls.ready
        len_hatcheries = self.townhalls.ready.amount

        if self.units(UnitTypeId.QUEEN).amount < len_hatcheries * 4:
            if self.can_afford(UnitTypeId.QUEEN) and self.structures(
                    UnitTypeId.SPAWNINGPOOL).ready.exists and not self.already_pending(UnitTypeId.QUEEN):
                self.train(UnitTypeId.QUEEN)

        for hatchery in all_hatcheries:
            queens_nearby = self.units(UnitTypeId.QUEEN).closer_than(8, hatchery)
            if not queens_nearby.exists and self.base_being_attacked == False:
                if self.can_afford(UnitTypeId.QUEEN) and self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists:
                    self.train(UnitTypeId.QUEEN)

            if self.hatchery_queen_pairs.get(hatchery.tag) is None:
                queens_nearby = self.units(UnitTypeId.QUEEN).idle.closer_than(8, hatchery)
                if queens_nearby:
                    assignable_queens = [q for q in queens_nearby if
                                         q.energy >= 25 and q.tag not in self.hatchery_queen_pairs.values()]
                    if assignable_queens:
                        closest_queen = assignable_queens[0]
                        self.hatchery_queen_pairs[hatchery.tag] = closest_queen.tag

            queen_tag = self.hatchery_queen_pairs.get(hatchery.tag)
            if queen_tag is not None:
                queen = self.units(UnitTypeId.QUEEN).find_by_tag(queen_tag)
                if queen:
                    abilities = await self.get_available_abilities(queen)
                    if AbilityId.EFFECT_INJECTLARVA in abilities:
                        queen(AbilityId.EFFECT_INJECTLARVA, hatchery)
                else:
                    # print("Queen dead")
                    del self.hatchery_queen_pairs[hatchery.tag]

    async def queen_spread(self):
        hatcheries = self.townhalls(UnitTypeId.HATCHERY) | self.townhalls(UnitTypeId.LAIR) | self.townhalls(
            UnitTypeId.HIVE)
        self.existing_hatchery_locations = []
        for label, coordinate in self.mineral_location_labels_reverse.items():
            hatchery = hatcheries.closer_than(8, Point2(coordinate)).ready
            if hatchery.exists:
                self.existing_hatchery_locations.append(label)

        print("existing_hatchery_locations:", self.existing_hatchery_locations)

        spread_sequence_A = ["A1", "A2", "A3", "B5"]
        spread_sequence_B = ["B1", "B2", "B3", "A5"]
        spread_sequence = spread_sequence_A if self.start_location_label == "A1" else spread_sequence_B

        for queen in self.units(UnitTypeId.QUEEN).idle:
            if queen.tag not in self.hatchery_queen_pairs.values():
                if queen.energy >= 25:
                    if queen.tag not in self.queen_spread_progress:
                        self.queen_spread_progress[queen.tag] = 0
                    current_progress = self.queen_spread_progress[queen.tag]  # 0, 1, 2

                    if current_progress >= len(spread_sequence):
                        continue

                    current_target_label = spread_sequence[current_progress]  # "A1", "A2", "A4", "A3", "A7", "A4", "B4"
                    # print("current_target_label:", current_target_label)
                    next_target_label = spread_sequence[(current_progress + 1) % len(spread_sequence)]
                    # print("next_target_label:", next_target_label)
                    current_target = Point2(self.mineral_location_labels_reverse[current_target_label])
                    next_target = Point2(self.mineral_location_labels_reverse[next_target_label])

                    if self.start_location_label == "A1":
                        if next_target_label in ["B4"] and not await self.is_hatchery_ready_at(next_target_label):
                            continue
                    elif self.start_location_label == "B1":
                        if next_target_label in ["A4"] and not await self.is_hatchery_ready_at(next_target_label):
                            continue

                    spread_position = await self.find_creep_placement(AbilityId.BUILD_CREEPTUMOR_QUEEN,
                                                                      current_target.towards(next_target,
                                                                                             self.spread_distance))

                    if spread_position:
                        queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, spread_position)
                        self.queen_spread_progress[queen.tag] = current_progress + 1
                        self.spread_distance = self.spread_distance + 3

    async def find_creep_placement(self, ability, center, max_radius=5, step=1):
        for r in range(0, max_radius, step):
            position = await self.find_placement(ability, center, max_distance=r)
            if position:
                return position
        return None

    async def is_hatchery_ready_at(self, location_label):
        target_location = Point2(self.mineral_location_labels_reverse[location_label])
        hatcheries = self.units(UnitTypeId.HATCHERY).ready
        for hatchery in hatcheries:
            if hatchery.position.to2.distance_to(target_location) < 5:  # 5可根据实际情况调整为合适的距离
                return True
        return False

    def get_high_priority_targets_roach(self, enemies):
        high_priority = enemies.of_type({UnitTypeId.SIEGETANK, UnitTypeId.THOR, UnitTypeId.MARAUDER})
        if high_priority.exists:
            return high_priority
        return enemies

    def position_around_unit(self, pos: Union[Unit, Point2, Point3], distance: int = 1, step_size: int = 1,
                             exclude_out_of_bounds: bool = True):
        pos = pos.position.rounded
        positions = {
            pos.offset(Point2((x, y)))
            for x in range(-distance, distance + 1, step_size) for y in range(-distance, distance + 1, step_size)
            if (x, y) != (0, 0)
        }
        # filter positions outside map size
        if exclude_out_of_bounds:
            positions = {
                p
                for p in positions
                if 0 <= p[0] < self.game_info.pathing_grid.width and 0 <= p[1] < self.game_info.pathing_grid.height
            }
        return positions

    async def Roach_ReflexNet(self):
        # print("Roach_ReflexNet")
        for roach in self.units(UnitTypeId.ROACH):
            enemies_in_range = self.enemy_units.filter(lambda u: u.distance_to(roach) < 9)
            if enemies_in_range:
                if roach.weapon_cooldown == 0:
                    high_priority_targets = self.get_high_priority_targets_roach(enemies_in_range)
                    target = min(high_priority_targets, key=lambda u: u.health + u.shield)
                    roach.attack(target)

                else:
                    stutter_step_positions = self.position_around_unit(roach, distance=4)
                    # filter in pathing grid
                    stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}
                    # find position furthest away from enemies and closest to unit
                    enemies_in_range = self.enemy_units.filter(lambda u: roach.target_in_range(u, -0.5))

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(roach),
                        )
                        roach.move(retreat_position)

    async def Ravager_ReflexNet(self):
        # print("Ravager_ReflexNet")
        for ravager in self.units(UnitTypeId.RAVAGER):
            enemies_in_range = self.enemy_units.filter(lambda u: u.distance_to(ravager) < 9)
            if enemies_in_range:
                high_priority_targets = self.get_high_priority_targets_roach(enemies_in_range)
                if high_priority_targets:
                    target = min(high_priority_targets, key=lambda t: t.health + t.shield)

                    if ravager(AbilityId.EFFECT_CORROSIVEBILE, target.position):
                        # Ravager weapon is ready, find the highest priority target
                        stutter_step_positions = self.position_around_unit(ravager, distance=4)

                        # filter in pathing grid
                        stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}

                        # find position furthest away from enemies and closest to unit
                        enemies_in_range = self.enemy_units.filter(lambda u: ravager.target_in_range(u, -0.5))

                        if stutter_step_positions and enemies_in_range:
                            retreat_position = max(
                                stutter_step_positions,
                                key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(ravager),
                            )
                            ravager.move(retreat_position)
                else:
                    stutter_step_positions = self.position_around_unit(ravager, distance=4)

                    # filter in pathing grid
                    stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}

                    # find position furthest away from enemies and closest to unit
                    enemies_in_range = self.enemy_units.filter(lambda u: ravager.target_in_range(u, -0.5))

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(ravager),
                        )
                        ravager.move(retreat_position)

    async def Hydralisk_ReflexNet(self):
        # print("Hydralisk_ReflexNet")
        if self.units(UnitTypeId.HYDRALISK).ready.exists:
            for hydralisk in self.units(UnitTypeId.HYDRALISK).ready:
                threats = self.enemy_units.closer_than(6, hydralisk)
                if threats:
                    # print("hydralisk detected enemy!")
                    medivac = threats.filter(lambda unit: unit.type_id == UnitTypeId.MEDIVAC)
                    if medivac.exists:
                        medivac_attack = medivac.closest_to(hydralisk)
                        # print("hydralisk attack medivac!")
                        hydralisk.attack(medivac_attack)

    async def Ultralisk_ReflexNet(self):
        # print("Ultralisk_ReflexNet")
        if self.structures(UnitTypeId.ULTRALISKCAVERN).ready.exists:
            ultralisk_num = 0
            if self.game_stage == 0:
                ultralisk_num = self.early_ultralisk_num
            elif self.game_stage == 1:
                ultralisk_num = self.mid_ultralisk_num
            elif self.game_stage == 2:
                ultralisk_num = self.late_ultralisk_num

            if self.units(UnitTypeId.ULTRALISK).amount < ultralisk_num:
                if self.units(UnitTypeId.LARVA).exists:
                    larva = self.units(UnitTypeId.LARVA).random
                    larva.train(UnitTypeId.ULTRALISK)

    def get_high_priority_targets_corruptor(self, enemies):
        high_priority = enemies.of_type({UnitTypeId.MEDIVAC, UnitTypeId.RAVEN})
        if high_priority.exists:
            return high_priority
        return enemies

    def get_high_priority_targets_infestor(self, enemies):
        high_priority = enemies.of_type({UnitTypeId.MARINE, UnitTypeId.MARAUDER})
        if high_priority.exists:
            return high_priority
        return enemies

    async def Corruptor_ReflexNet(self):
        # print("Corruptor_ReflexNet")
        for corruptor in self.units(UnitTypeId.CORRUPTOR):
            if self.enemy_units:
                if corruptor.weapon_cooldown == 0:
                    enemies_in_range = self.enemy_units.filter(lambda u: corruptor.target_in_range(u))
                    if enemies_in_range:
                        high_priority_targets = self.get_high_priority_targets_corruptor(enemies_in_range)
                        target = min(high_priority_targets, key=lambda u: u.health + u.shield)
                        corruptor.attack(target)

                else:
                    stutter_step_positions = self.position_around_unit(corruptor, distance=4)
                    # filter in pathing grid
                    stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}
                    # find position furthest away from enemies and closest to unit
                    enemies_in_range = self.enemy_units.filter(lambda u: corruptor.target_in_range(u, -0.5))

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(corruptor),
                        )
                        corruptor.move(retreat_position)

        if self.units(UnitTypeId.CORRUPTOR).exists and self.supply_left > 2:
            if self.structures(UnitTypeId.GREATERSPIRE).ready.exists and self.structures(UnitTypeId.HIVE).ready.exists:
                corruptor = self.units(UnitTypeId.CORRUPTOR).random
                corruptor(AbilityId.TRAIN_SWARMHOST)

    async def infestor_ReflexNet(self):
        # print("infestor_ReflexNet")
        if self.structures(UnitTypeId.INFESTATIONPIT).ready.exists and self.structures(
                UnitTypeId.INFESTATIONPIT).ready.exists:
            infestor_num = 0
            if self.game_stage == 0:
                infestor_num = self.early_infestor_num
            elif self.game_stage == 1:
                infestor_num = self.mid_infestor_num
            elif self.game_stage == 2:
                infestor_num = self.late_infestor_num

            if self.units(UnitTypeId.INFESTOR).amount <= infestor_num and self.units(UnitTypeId.LARVA).exists:
                larva = self.units(UnitTypeId.LARVA).random
                larva.train(UnitTypeId.INFESTOR)

        for infestor in self.units(UnitTypeId.INFESTOR):
            enemies_in_range = self.enemy_units.filter(lambda u: u.distance_to(infestor) < 9)
            if enemies_in_range:
                high_priority_targets = self.get_high_priority_targets_infestor(enemies_in_range)
                target = min(high_priority_targets, key=lambda t: t.health + t.shield)

                if infestor(AbilityId.FUNGALGROWTH_FUNGALGROWTH, target.position):
                    # Ravager weapon is ready, find the highest priority target
                    stutter_step_positions = self.position_around_unit(infestor, distance=5)

                    # filter in pathing grid
                    stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}

                    # find position furthest away from enemies and closest to unit
                    enemies_in_range = self.enemy_units.filter(lambda u: infestor.target_in_range(u, -0.5))

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(infestor),
                        )
                        infestor.move(retreat_position)

                else:
                    stutter_step_positions = self.position_around_unit(infestor, distance=4)
                    # filter in pathing grid
                    stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}
                    # find position furthest away from enemies and closest to unit
                    enemies_in_range = self.enemy_units.filter(lambda u: infestor.target_in_range(u, -0.5))

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(infestor),
                        )
                        infestor.move(retreat_position)

    async def handle_commands(self):
        # if self.start_location_label == "A1":
        #     base_location = Point2(self.mineral_location_labels_reverse["A1"])
        # elif self.start_location_label == "B1":
        #     base_location = Point2(self.mineral_location_labels_reverse["B1"])

        filtered_commands = []

        for command_list in self.parsed_commands:
            if len(command_list) != 3:
                continue

            action, location = command_list[1], command_list[2]
            if 'Build' in action and ', ' in location:
                building, loc_code = location.rsplit(', ', 1)
                base_location_coords = self.mineral_location_labels_reverse.get(loc_code)
                if base_location_coords and "Hatchery" in command_list[2]:
                    base_location = Point2(base_location_coords)
                    hatchery = self.townhalls.closer_than(2.0, base_location).ready
                    if hatchery.exists:
                        print("Hatchery exists in", loc_code)
                        self.waiting_for_hatchery = False
                        continue
                    else:
                        if "Hatchery" in building and self.minerals <= 400:
                            self.waiting_for_hatchery = True
                            print("self.waiting_for_hatchery set to True")
            filtered_commands.append(command_list)
        self.parsed_commands = filtered_commands
        print("filtered self.parsed_commands:", self.parsed_commands)

        for command_list in self.parsed_commands:
            i = self.parsed_commands.index(command_list)
            if "Drone" in command_list[0]:
                # print("Drone")
                location = self.check_loc(command_list[2])
                # print("command_list[2] ", command_list[2])
                # print("location ", location)
                if location == "":
                    if self.start_location_label == "A1":
                        location = "A1"
                    elif self.start_location_label == "B1":
                        location = "B1"
                await self.build_buildings(command_list[2], i, location)

            elif "Larva" in command_list[0]:
                # print("Larva")
                await self.build_units(command_list[2], i)

            elif "Overlord" in command_list[0]:
                location = self.check_loc(command_list[2])
                await self.overlord_scout(i, location)

            elif "Zergling" in command_list[0]:
                action = command_list[1]
                location = self.check_loc(command_list[2])
                await self.zergling_command(command_list[2], action, i, location)

            elif "Roach" in command_list[0]:
                action = command_list[1]
                location = self.check_loc(command_list[2])
                await self.roach_command(command_list[2], action, i, location)

            else:
                if i < len(self.parsed_commands):
                    del self.parsed_commands[i]
                    print("Deleted command_list at index", i)

    async def build_drones_for_second_hatchery(self):
        second_hatchery = self.townhalls.ready.exclude_type({UnitTypeId.HATCHERY}).closest_to(self.start_location)
        if second_hatchery and second_hatchery.assigned_harvesters < second_hatchery.ideal_harvesters:
            larvas = self.units(UnitTypeId.LARVA).closer_than(10.0, second_hatchery)
            if larvas.exists and self.can_afford(UnitTypeId.DRONE):
                larva = larvas.random
                larva.train(UnitTypeId.DRONE)


def extract_units_info(stage_info):
    early_match = re.search(r'Early stage:(.*?)Mid stage:', stage_info, re.DOTALL)
    mid_match = re.search(r'Mid stage:(.*?)Late stage:', stage_info, re.DOTALL)
    late_match = re.search(r'Late stage:(.*)', stage_info, re.DOTALL)

    early_stage_text = early_match.group(1).strip() if early_match else ""
    mid_stage_text = mid_match.group(1).strip() if mid_match else ""
    late_stage_text = late_match.group(1).strip() if late_match else ""

    pattern = r'(?<=Zergling: )\d+|(?<=Baneling: )\d+|(?<=Roach: )\d+|(?<=Ravager: )\d+|(?<=Hydralisk: )\d+|(?<=Infestor: )\d+|(?<=Swarm host: )\d+|(?<=Mutalisk: )\d+|(?<=Corruptor: )\d+|(?<=Viper: )\d+|(?<=Ultralisk: )\d+|(?<=Brood Lord: )\d+'

    def extract_numbers(text):
        matches = re.findall(pattern, text)
        return [int(match) for match in matches]

    early_stage_units = extract_numbers(early_stage_text)
    mid_stage_units = extract_numbers(mid_stage_text)
    late_stage_units = extract_numbers(late_stage_text)

    return early_stage_units, mid_stage_units, late_stage_units


def assign_values(units_list):
    zergling_num = units_list[0]
    baneling_num = units_list[1]
    roach_num = units_list[2]
    ravager_num = units_list[3]
    hydralisk_num = units_list[4]
    infestor_num = units_list[5]
    swarm_host_num = units_list[6]
    mutalisk_num = units_list[7]
    corruptor_num = units_list[8]
    viper_num = units_list[9]
    ultralisk_num = units_list[10]
    brood_lord_num = units_list[11]

    return (zergling_num, baneling_num, roach_num, ravager_num,
            hydralisk_num, infestor_num, swarm_host_num, mutalisk_num,
            corruptor_num, viper_num, ultralisk_num, brood_lord_num)


def main():
    stage_info = overmind_brain_initial()
    print(stage_info)

    early_units, mid_units, late_units = extract_units_info(stage_info)
    print("Early stage units:", early_units)
    early_values = assign_values(early_units)

    print("Mid stage units:", mid_units)
    mid_values = assign_values(mid_units)

    print("Late stage units:", late_units)
    late_values = assign_values(late_units)

    strategy = overmind_brain_initial2()
    print(strategy)

    results = {}
    for line in strategy.strip().split('\n'):
        question, answer = line.split(':')
        question = question.strip()
        answer = answer.strip()
        if answer == 'False':
            results[question] = False
        elif answer == 'True':
            results[question] = True

    drone_attack = results['Question 1']
    counterattack = results['Question 2']
    # print("drone_attack:", drone_attack)
    # print("counterattack:", counterattack)

    output1 = overmind_brain_1()
    print(output1)
    matches = re.findall(r'\(.*?\)->\(.*?\)->\(.*?\)', output1)

    command_first = []
    for match in matches:
        command_first.append(match)

    run_game(
        maps.get("AutomatonLE"),
        [Bot(Race.Zerg, SwarmBrain(command_first, early_values, mid_values, late_values, drone_attack, counterattack)),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=True, save_replay_as="./videos/ZvT_Medium.SC2Replay"
    )

    # run_game(
    #     maps.get("AutomatonLE"),
    #     [Human(Race.Terran),
    #         Bot(Race.Zerg, SwarmBrain(early_values, mid_values, late_values, drone_attack, counterattack))],
    #     realtime=True, save_replay_as="./videos/ZvT_Human.SC2Replay"
    # )


if __name__ == '__main__':
    main()
