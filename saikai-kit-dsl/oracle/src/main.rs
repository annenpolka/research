//! Oracle for the kit DSL prototype: feeds setting text to saikai-rules'
//! own parsers and prints the canonical text they give back.
//! stdin: `<KNOB>\t<value>` per line; stdout: `<KNOB>\tok\t<to_text>` or `<KNOB>\terr\t<error>`.
//! `dump` as the first argument prints the runtime's `on` tables rebuilt from the same constants.
use std::io::{self, BufRead};

use saikai_rules::experiment::{ProvisionalKit, parse_mion, perf as names};
use saikai_rules::weapon::{Carry, Cap, Inertia, Table as Inertia_};
use saikai_rules::loco::cost::Table as Cost;
use saikai_rules::{air, ammo, body, cancel, charge, guard, homing, landing, melee, react, step, ukemi};

fn check(knob: &str, v: &str) -> Result<String, String> {
    macro_rules! p { ($e:expr) => { $e.map(|s| s.to_text()).map_err(|e| format!("{e:?}")) } }
    match knob {
        "SAIKAI_KIT" => {
            if v.split(|c: char| c.is_whitespace() || c == ',').find(|s| !s.is_empty()) == Some("mion") {
                parse_mion(v).map(|()| "mion".to_owned()).map_err(|e| format!("{e:?}"))
            } else {
                ProvisionalKit::parse(v).map(|k| {
                    let perfs: Vec<String> = k.kit().perfs().iter().map(|p| p.name().to_owned()).collect();
                    format!("{}\tperfs={}", k.to_text(), perfs.join(","))
                }).map_err(|e| format!("{e:?}"))
            }
        }
        "SAIKAI_STEP" => p!(step::Settings::parse(v)),
        "SAIKAI_LOCO" => p!(saikai_rules::loco::settings::Settings::parse(v)),
        "SAIKAI_AIR" => p!(air::Setting::parse(v)),
        "SAIKAI_INERTIA" => if matches!(v.trim(), "on" | "1") { Ok(provisional_inertia().to_text()) } else { p!(Inertia_::parse(v)) },
        "SAIKAI_BOOST_COST" => if matches!(v.trim(), "on" | "1") { Ok(Cost::provisional().to_text()) } else { p!(Cost::parse(v)) },
        "SAIKAI_CHARGE" => p!(charge::Settings::parse(v)),
        "SAIKAI_CANCEL" => p!(cancel::Settings::parse(v)),
        "SAIKAI_AMMO" => p!(ammo::Settings::parse(v)),
        "SAIKAI_MELEE" => p!(melee::Settings::parse(v)),
        "SAIKAI_GUARD" => p!(guard::Settings::parse(v)),
        "SAIKAI_LANDING" => p!(landing::Settings::parse(v)),
        "SAIKAI_UKEMI" => p!(ukemi::Settings::parse(v)),
        "SAIKAI_REACT" => p!(react::Settings::parse(v)),
        "SAIKAI_HOMING" => p!(homing::Settings::parse(v)),
        "SAIKAI_BODY" => p!(body::Setting::parse(v)),
        other => Err(format!("no rules parser for {other}")),
    }
}

/// `saikai-runtime::weapon::provisional()` rebuilt from the same constants
/// (the runtime crate does not build off Windows).
fn provisional_inertia() -> Inertia_ {
    let sub = Inertia { cap: Cap { h: None, v: Some(26_666_667) }, ..Inertia::shares(100, 95, 95) };
    Inertia_::with_rows(Carry::Stop(Inertia::MBON_DEFAULT), &[(names::NATA_EX, Carry::Own)])
        .with("melee", Carry::Own)
        .with("main", Carry::Move)
        .with("turn_around", Carry::Stop(Inertia::shares(100, 92, 95)))
        .with("sub_shot", Carry::Stop(sub))
        .with("special_shot", Carry::Stop(Inertia::shares(100, 95, 95)))
        .with("special_melee", Carry::Stop(Inertia::shares(100, 95, 97)))
        .with("charge_shot", Carry::Stop(Inertia::MBON_DEFAULT))
        .with("down_melee", Carry::Own)
}

fn main() {
    if std::env::args().nth(1).as_deref() == Some("dump") {
        println!("INERTIA_ON\t{}", provisional_inertia().to_text());
        println!("BOOST_COST_ON\t{}", Cost::provisional().to_text());
        println!("PERF_ALL\t{}", names::ALL.iter().map(|p| p.name()).collect::<Vec<_>>().join(","));
        println!("PERF_WATER\t{}", names::WATER.iter().map(|p| p.name()).collect::<Vec<_>>().join(","));
        for (k, v) in [("SAIKAI_STEP","on"),("SAIKAI_LOCO","on"),("SAIKAI_AIR","on"),("SAIKAI_CHARGE","on"),("SAIKAI_CANCEL","on"),("SAIKAI_AMMO","on"),("SAIKAI_MELEE","on"),("SAIKAI_GUARD","on"),("SAIKAI_LANDING","on"),("SAIKAI_UKEMI","on"),("SAIKAI_REACT","on"),("SAIKAI_HOMING","on"),("SAIKAI_BODY","on")] {
            match check(k, v) { Ok(t) => println!("DEFAULT\t{k}\t{t}"), Err(e) => println!("DEFAULT\t{k}\tERR {e}") }
        }
        return;
    }
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let Some((knob, v)) = line.split_once('\t') else { continue };
        match check(knob, v) {
            Ok(t) => println!("{knob}\tok\t{t}"),
            Err(e) => println!("{knob}\terr\t{e}"),
        }
    }
}
