<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<gameSystem id="my-tactical-game-gst" name="Lead Ledger" revision="1" battleScribeVersion="2.03" xmlns="http://www.battlescribe.net/schema/gameSystemSchema">
  <costTypes>
    <costType id="mp-cost" name="MP" defaultCostLimit="-1.0" hidden="false"/>
    <costType id="mats-cost" name="Mats" defaultCostLimit="-1.0" hidden="false"/>
  </costTypes>
  <profileTypes>
    <profileType id="unit-profile-id" name="Unit">
      <characteristicTypes>
        <characteristicType id="movement" name="Mov"/>
        <characteristicType id="armor" name="Arm"/>
        <characteristicType id="control" name="Con"/>
        <characteristicType id="health" name="HP"/>
      </characteristicTypes>
    </profileType>
    <profileType id="weapon-profile-id" name="Weapons">
      <characteristicTypes>
        <characteristicType id="weapon-range" name="R"/>
        <characteristicType id="weapon-none" name="N"/>
        <characteristicType id="weapon-light" name="L"/>
        <characteristicType id="weapon-medium" name="M"/>
        <characteristicType id="weapon-heavy" name="H"/>
        <characteristicType id="weapon-fortification" name="F"/>
        <characteristicType id="weapon-keywords" name="Keywords"/>
      </characteristicTypes>
    </profileType>
    <profileType id="b88b-b6ca-13c2-bb58" name="Abilities">
      <characteristicTypes>
        <characteristicType id="71a6-c11b-3c40-dde8" name="Description"/>
      </characteristicTypes>
    </profileType>
  </profileTypes>
  <categoryEntries>
    <categoryEntry id="inf" name="Infantry" hidden="false"/>
    <categoryEntry id="veh" name="Vehicle" hidden="false"/>
    <categoryEntry id="sup" name="Support" hidden="false"/>
    <categoryEntry id="apc" name="APC" hidden="false"/>
    <categoryEntry id="b43b-a848-fcd3-f503" name="Light Tank" hidden="false"/>
    <categoryEntry id="201c-1576-d588-aad5" name="IFV" hidden="false"/>
    <categoryEntry id="dc81-ab91-495d-0042" name="MBT" hidden="false"/>
    <categoryEntry id="4972-4598-7035-2b18" name="SPG" hidden="false"/>
    <categoryEntry id="b9a5-fc14-d873-704f" name="Armored Car" hidden="false"/>
    <categoryEntry id="b9a5-fc14-d873-7045" name="Artillery" hidden="false"/>
  </categoryEntries>
  <forceEntries>
    <forceEntry id="army-list-gst" name="Army List (GST)" hidden="true"/>
  </forceEntries>
  <sharedRules>
    <rule id="5475-29e2-85c2-9a76" name="Assault" hidden="false">
      <description>When you Advance a unit with an Assault weapon, you may then Minor it to shoot, and only weapons with Assault can shoot.</description>
    </rule>
    <rule id="5475-29e2-85c2-9b45" name="Linked" hidden="false">
      <description>Linked weapons can only shoot at targets in the same tile or adjacent tiles to the target of other Linked weapons.

Resolve Linked weapons in any order.
- The first Linked weapon has no restriction.
- Each following Linked weapon's target must be within 1 range of all previous targets of Linked weapons.</description>
    </rule>
    <rule id="8956-be22-469d-2391" name="Transport" hidden="false">
      <description>Can transport Infantry.</description>
    </rule>
    <rule id="5475-29e2-85c2-9a89" name="Long" hidden="false">
      <description>Long weapons have higher Range than normal (+2, included in the weapon profile).</description>
    </rule>
    <rule id="5475-29e2-85c2-9b76" name="Frontal" hidden="false">
      <description>Frontal weapons can only target enemies/tiles in the unit's front arc.
      
The front arc is the tile directly ahead and any tiles at least partially within the 60° cone extending from that edge.</description>
    </rule>
    <rule id="5475-29e2-85c2-9b79" name="Precision" hidden="false">
      <description>Precision weapons can target units within Fortifications and ignore Evasion rolls.</description>
    </rule>
    <rule id="5475-29e2-85c2-9b71" name="HE" hidden="false">
      <description>HE weapons have better N penetration, worse armor penetration and more F damage than normal (+1, -1 and +1 respectively, included in the weapon profile)</description>
    </rule>
    <rule id="5475-29e2-85c2-9b72" name="Blast" hidden="false">
      <description>Blast weapons target tiles, and deal damage to every unit within that tile.</description>
    </rule>
    <rule id="5475-29e2-85c2-9b73" name="Indirect Fire" hidden="false">
      <description>Indirect Fire weapons do not need LoS to shoot at targets.</description>
    </rule>
    <rule id="5475-29e2-85c2-9b74" name="Loading X" hidden="false">
      <description>Loading weapons have an Ammo characteristic (X), and consume 1 Ammo each time they shoot.

At the beginning of each cycle, restore all Loading weapons' Ammo to full.</description>
    </rule>
  </sharedRules>
  <sharedProfiles>
    <profile id="6851-f823-5b74-bebb" name="NERA Armor" hidden="false" typeId="b88b-b6ca-13c2-bb58" typeName="Abilities">
      <characteristics>
        <characteristic name="Description" typeId="71a6-c11b-3c40-dde8">-2AP to HEAT, Tandem, HESH and RPGs targetting this unit</characteristic>
      </characteristics>
    </profile>
    <profile id="6851-f823-5b74-bebc" name="Brittle" hidden="false" typeId="b88b-b6ca-13c2-bb58" typeName="Abilities">
      <characteristics>
        <characteristic name="Description" typeId="71a6-c11b-3c40-dde8">+1AP to all shots that target this unit.</characteristic>
      </characteristics>
    </profile>
    <profile id="58ec-2f03-cfde-51bd" name="Sloped Armor" hidden="false" typeId="b88b-b6ca-13c2-bb58" typeName="Abilities">
      <characteristics>
        <characteristic name="Description" typeId="71a6-c11b-3c40-dde8">-4AP to AC; -2AP to AP and RPGs targetting this unit</characteristic>
      </characteristics>
    </profile>
    <profile id="58ec-2f03-cfde-51ba" name="Slat Armor" hidden="false" typeId="b88b-b6ca-13c2-bb58" typeName="Abilities">
      <characteristics>
        <characteristic name="Description" typeId="71a6-c11b-3c40-dde8">-4AP to RPG; -2AP to HESH and HEAT targetting this unit</characteristic>
      </characteristics>
    </profile>
  </sharedProfiles>
</gameSystem>