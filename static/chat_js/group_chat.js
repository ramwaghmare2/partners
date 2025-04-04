let selectedMembers = [];

    document.addEventListener("DOMContentLoaded", function() {
        document.querySelectorAll(".add-user-btn").forEach(button => {
            button.addEventListener("click", function() {
                let userId = this.getAttribute("data-user-id");
                let userName = this.getAttribute("data-user-name");
                let userMobile = this.getAttribute("data-user-mobile"); // Keep consistent with 'mobile'
                let userRole = this.getAttribute("data-user-role");

                console.log("User ID:", userId);
                console.log("User Name:", userName);
                console.log("User Mobile:", userMobile);
                console.log("User Role:", userRole);

                // Ensure uniqueness via mobile number
                if (!selectedMembers.some(member => member.mobile === userMobile)) {
                    selectedMembers.push({
                        userid: userId,
                        name: userName,
                        mobile: userMobile, // Use 'mobile' consistently
                        role: userRole
                    });
                    updateSelectedMembers();
                }
            });
        });

        document.getElementById("createGroupBtn").addEventListener("click", function() {
            let groupName = document.getElementById("groupName").value;
            let description = document.getElementById("groupDescription").value;
        
            // Get the file input element for the group photo
            let groupPhotoInput = document.getElementById("groupPhoto");
            let groupPhotoFile = groupPhotoInput.files[0];
            let groupPhotoBase64 = null;
        
            // If a file is selected, convert it to base64
            if (groupPhotoFile) {
                let reader = new FileReader();
                reader.onloadend = function() {
                    groupPhotoBase64 = reader.result;
                    submitGroupData();
                };
                reader.readAsDataURL(groupPhotoFile);  // Convert image to base64
            } else {
                submitGroupData();
            }
        
            // Submit the group data to the server
            function submitGroupData() {
                if (!groupName || selectedMembers.length === 0) {
                    alert("Please enter a group name and select at least one member.");
                    return;
                }
        
                let groupData = {
                    group_name: groupName,
                    description: description,
                    members: selectedMembers.map(member => ({
                        id: member.userid,
                        mobile: member.mobile, // Use 'mobile' instead of 'contact'
                        role: member.role
                    }))
                };
        
                // If a photo was selected, include it in the group data
                if (groupPhotoBase64) {
                    groupData.group_photo = groupPhotoBase64;
                }
        
                // Send the request
                fetch("/chat/create_group", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(groupData)
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    location.reload();  // Reload the page after group creation
                })
                .catch(error => console.error("Error:", error));
            }
        });
        
    });

    function updateSelectedMembers() {
        let container = document.getElementById("selectedMembers");
        container.innerHTML = "";

        selectedMembers.forEach(member => {
            let div = document.createElement("div");
            div.classList.add("d-flex", "justify-content-between", "align-items-center", "mb-1");
            div.innerHTML = `
                <span>${member.name} (${member.mobile})</span>
                <button type="button" class="btn btn-danger btn-sm" onclick="removeMember('${member.mobile}')">
                    <i class="fas fa-minus"></i>
                </button>
            `;
            container.appendChild(div);
        });
    }

    function removeMember(mobile) {
        selectedMembers = selectedMembers.filter(member => member.mobile !== mobile);
        updateSelectedMembers();
    }


    let newParticipants = []; // Store newly added users
    let removedParticipants = []; // Store removed users
    
    function openEditGroupModal() {
        let chatWindow = document.getElementById("chatWindow");
        let groupId = chatWindow.getAttribute("data-group-id");
        let groupName = document.getElementById("chatTitle").textContent;
    
        if (!groupId) {
            alert("No group selected!");
            return;
        }
    
        document.getElementById("groupId").value = groupId;
        document.getElementById("groupNamemodel").value = groupName;
    
        fetch(`/chat/get_group_details?group_id=${groupId}`)
            .then(response => response.json())
            .then(data => {
                console.log("Fetched Group Data:", data);
    
                if (data.error) {
                    alert("Error: " + data.error);
                    return;
                }
    
                document.getElementById("groupNamemodel").value = data.name || "No Name";
                document.getElementById("groupDescriptionmodel").value = data.description || "";
    
                let participantsContainer = document.getElementById("groupParticipantsContainer");
                participantsContainer.innerHTML = ""; 
    
                data.members.forEach(member => {
                    let participantDiv = document.createElement("div");
                    participantDiv.classList.add("col-md-4", "mb-2", "d-flex", "align-items-center");
                    participantDiv.setAttribute("data-member-id", member.id);
    
                    participantDiv.innerHTML = `
                        <div class="p-2 border rounded d-flex justify-content-between w-100">
                            <div>
                                <span>${member.name}</span>  
                                <div class="text-muted">${member.role}</div>  
                            </div>
                            <button class="btn btn-danger btn-sm" style="height: 30px; margin-top: 8px;" 
                                    onclick="removeExistingMember('${member.id}')">
                                <i class="fas fa-minus"></i>
                            </button>
                        </div>
                    `;
                    participantsContainer.appendChild(participantDiv);
                });
            })
            .catch(error => console.error("Error fetching group details:", error));
    
        let modal = new bootstrap.Modal(document.getElementById("editGroupModal"));
        modal.show();
    }
    
    // Edit group model Javascript
    function showAddMembers() {
        let groupId = document.getElementById("groupId").value;
        if (!groupId) {
            alert("Group ID is missing!");
            return;
        }
    
        fetch(`/chat/get_available_users/${groupId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert("Error: " + data.error);
                    return;
                }
    
                let availableUsersContainer = document.getElementById("availableUsersContainer");
                availableUsersContainer.innerHTML = ""; 
    
                if (data.users.length === 0) {
                    availableUsersContainer.innerHTML = `<p class="text-muted">No available users to add.</p>`;
                    return;
                }
    
                data.users.forEach(user => {
                    let userDiv = document.createElement("div");
                    userDiv.classList.add("d-flex", "justify-content-between", "align-items-center", "p-2", "border", "rounded", "mb-2");
                    userDiv.innerHTML = `
                        <div>
                            <strong>${user.name}</strong> (${user.role})<br>
                            <small>${user.email} | ${user.contact}</small>
                        </div>
                        <button class="btn btn-success btn-sm" onclick="addUserToGroup('${user.id}', '${user.role}', '${user.contact}', '${user.name}')">
                            <i class="fas fa-plus"></i>
                        </button>
                    `;
                    availableUsersContainer.appendChild(userDiv);
                });
    
                document.getElementById("addMembersSection").style.display = "block";
            })
            .catch(error => console.error("Error fetching available users:", error));
    }
    
    
    function saveGroupChanges() {
        let groupId = document.getElementById("groupId").value;
        let groupName = document.getElementById("groupNamemodel").value.trim();
        let groupDescription = document.getElementById("groupDescriptionmodel").value.trim();
    
        if (!groupId) {
            alert("Group ID is missing!");
            return;
        }
    
        let updateData = {
            group_id: groupId,
            removed_members: removedParticipants
        };
    
        if (groupName) updateData.group_name = groupName;
        if (groupDescription) updateData.group_description = groupDescription;
        if (newParticipants.length > 0) updateData.new_members = newParticipants;
    
        fetch("/chat/update_group", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updateData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
            } else {
                alert("Group updated successfully!");
                let modal = bootstrap.Modal.getInstance(document.getElementById("editGroupModal"));
                if (modal) modal.hide();
                location.reload();
            }
        })
        .catch(error => console.error("Error updating group:", error));
    }
    
    
    function addUserToGroup(userId, userRole, userContact, userName) {
        let participantsContainer = document.getElementById("groupParticipantsContainer");
    
        event.stopPropagation();  
        event.preventDefault();  
    
        if (newParticipants.some(user => user.id === userId)) {
            alert("User already added!");
            return;
        }
    
        newParticipants.push({ id: userId, role: userRole, contact: userContact });
    
        let participantDiv = document.createElement("div");
        participantDiv.classList.add("col-md-4", "mb-2", "d-flex", "align-items-center");
        participantDiv.setAttribute("data-user-id", userId);
    
        participantDiv.innerHTML = `
            <div class="p-2 border rounded d-flex justify-content-between w-100">
                <div>
                    <span>${userName}</span>
                    <div class="text-muted">${userRole}</div>
                </div>
                <button class="btn btn-danger btn-sm" onclick="removeNewMember('${userId}')" style="height: 30px; margin-top: 8px;">
                    <i class="fas fa-minus"></i>
                </button>
            </div>
        `;
    
        participantsContainer.appendChild(participantDiv);
    }
    
    
    function removeNewMember(userId) {
        newParticipants = newParticipants.filter(user => user.id !== userId);
        let userDiv = document.querySelector(`[data-user-id='${userId}']`);
        if (userDiv) {
            userDiv.remove();
        }
    }
    
    
    function removeExistingMember(userId) {
        removedParticipants.push(userId);
        let userDiv = document.querySelector(`[data-member-id='${userId}']`);
        if (userDiv) {
            userDiv.remove();
        }
    }