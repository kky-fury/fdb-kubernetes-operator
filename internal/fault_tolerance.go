/*
 * fault_tolerance.go
 *
 * This source file is part of the FoundationDB open source project
 *
 * Copyright 2021 Apple Inc. and the FoundationDB project authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package internal

// HasDesiredFaultTolerance checks if the cluster has the desired fault tolerance.
func HasDesiredFaultTolerance(expectedFaultTolerance int, maxZoneFailuresWithoutLosingData int, maxZoneFailuresWithoutLosingAvailability int) bool {
	// Only if both max zone failures for availability and data loss are greater or equal to the expected fault tolerance we know that we meet
	// our fault tolerance requirements.
	return maxZoneFailuresWithoutLosingData >= expectedFaultTolerance && maxZoneFailuresWithoutLosingAvailability >= expectedFaultTolerance
}
