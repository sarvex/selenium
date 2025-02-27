// Licensed to the Software Freedom Conservancy (SFC) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The SFC licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

use crate::downloads::read_content_from_link;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::error::Error;

pub const MIRROR_URL: &str =
    "https://raw.githubusercontent.com/SeleniumHQ/selenium/trunk/common/mirror/selenium";

#[derive(Serialize, Deserialize)]
pub struct Assets {
    pub browser_download_url: String,
}

#[derive(Serialize, Deserialize)]
pub struct SeleniumRelease {
    pub tag_name: String,
    pub assets: Vec<Assets>,
}

pub fn get_mirror_response(http_client: &Client) -> Result<Vec<SeleniumRelease>, Box<dyn Error>> {
    let content = read_content_from_link(http_client, MIRROR_URL.to_string())?;
    let mirror_response: Vec<SeleniumRelease> = serde_json::from_str(&content)?;
    Ok(mirror_response)
}
